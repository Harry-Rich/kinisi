"""
The Analyzer class is the main API interface for users to :py:mod:`kinisi`. 
Typically, it is expected that the user would access a specific :py:class:`Analyzer`,
such as the :py:class:`DiffusionAnalyzer`, which sub-class this class.

Note, that all of the :py:attr:`classmethod` functions for the :py:class:`Analyzer`
are intended for internal use. 
"""

from typing import Union, List
import numpy as np
import scipp as sc
from kinisi.parser import PymatgenParser, Parser

class Analyzer:
    """
    This class is the superclass for the :py:class:`kinisi.analyze.DiffusionAnalyzer`,
    :py:class:`kinisi.analyze.JumpDiffusionAnalyzer` and :py:class:`kinisi.analyze.ConductivityAnalyzer` classes.

    :param trajectory: The parsed trajectory from some input file. This will be of type :py:class:`Parser`, but
        the specifics depend on the parser that is used. 
    """
    def __init__(self, trajectory: Parser) -> None:
        self.trajectory = trajectory

    @classmethod
    def _from_Xdatcar(cls,
                      trajectory: Union['pymatgen.io.vasp.outputs.Xdatcar', List['pymatgen.io.vasp.outputs.Xdatcar']],
                      specie: Union['pymatgen.core.periodic_table.Element', 'pymatgen.core.periodic_table.Specie'],
                      time_step: sc.Variable,
                      step_skip: sc.Variable,
                      dtype: Union[str, None] = None,
                      dt: sc.Variable = None,
                      dimension: str = 'xyz',
                      distance_unit: sc.Unit = sc.units.angstrom,
                      progress: bool = True) -> 'Analyzer': 
        """
        Constructs the necessary :py:mod:`kinisi` objects for analysis from a single or a list of
        :py:class:`pymatgen.io.vasp.outputs.Xdatcar` objects.

        :param trajectory: The :py:class:`pymatgen.io.vasp.outputs.Xdatcar` or list of these that should be parsed. 
        :param specie: Specie to calculate diffusivity for as a String, e.g. :py:attr:`'Li'`.
        :param time_step: The input simulation time step, i.e., the time step for the molecular dynamics integrator. Note, 
            that this must be given as a :py:mod:`scipp`-type scalar. The unit used for the time_step, will be the unit 
            that is use for the time interval values.
        :param step_skip: Sampling freqency of the simulation trajectory, i.e., how many time steps exist between the
            output of the positions in the trajectory. Similar to the :py:attr:`time_step`, this parameter must be
            a :py:mod:`scipp` scalar. The units for this scalar should be dimensionless.
        :param dtype: If :py:attr:`trajectory` is a :py:class:`pymatgen.io.vasp.outputs.Xdatcar` object, this should
            be :py:attr:`None`. However, if a list of :py:class:`pymatgen.io.vasp.outputs.Xdatcar` objects is passed,
            then it is necessary to identify if these constitute a series of :py:attr:`consecutive` trajectories or
            a series of :py:attr:`identical` starting points with different random seeds, in which case the `dtype`
            should be either :py:attr:`consecutive` or :py:attr:`identical`.:
        :param dt: Time intervals to calculate the displacements over. Optional, defaults to a :py:mod:`scipp` array
            ranging from the smallest interval (i.e., time_step * step_skip) to the full simulation length, with 
            a step size the same as the smallest interval.
        :param dimension: Dimension/s to find the displacement along, this should be some subset of `'xyz'` indicating
            the axes of interest. Optional, defaults to `'xyz'`.
        :param distance_unit: The unit of distance in the simulation input. This should be a :py:mod:`scipp` unit and
            defaults to :py:attr:`sc.units.angstrom`.
        :param progress: Print progress bars to screen. Optional, defaults to :py:attr:`True`.
        """
        if dtype is None:
            p = PymatgenParser(trajectory.structures, specie, time_step, step_skip, dt, dimension, distance_unit, progress)
            return cls(p)
        elif dtype == 'identical':
            u = [PymatgenParser(f.structures, specie, time_step, step_skip, dt, dimension, distance_unit, progress) for f in trajectory]
            p = u[0]
            p.displacements = sc.concat([i.displacements for i in u], 'atom')
            return cls(p)
        elif dtype == 'consecutive':
            structures = _flatten_list([x.structures for x in trajectory])
            p = PymatgenParser(structures, specie, time_step, step_skip, dt, dimension, distance_unit, progress)
            return cls(p)
        
    @property
    def distributions(self) -> np.array:
        """
        :return: A distribution of samples for the linear relationship that can be used for easy
        plotting of credible intervals.
        """
        if self.diff.intercept is not None:
            return self.diff.gradient.values * self.mstd.coords['timestep'].values[:, np.newaxis] + self.diff.intercept.values
        else:
            return self.diff.gradient.values * self.mstd.coords['timestep'].values[:, np.newaxis]
        

def _flatten_list(this_list: list) -> list:
    """
    Flatten nested lists.

    :param this_list: List to be flattened

    :return: Flattened list
    """
    return [item for sublist in this_list for item in sublist]


def _stack_trajectories(u: sc.Variable) -> List[np.ndarray]:
    """
    If more than one trajectory is given, then they are stacked to give the appearance that there are
    additional atoms in the trajectory.

    :param u: Results from the parsing of each trajectory.

    :return: The stacked displacement list.
    """
    joint_disp_3d = []
    for i in range(len(u[0].disp_3d)):
        disp = np.zeros((u[0].disp_3d[i].shape[0] * len(u), u[0].disp_3d[i].shape[1], u[0].disp_3d[i].shape[2]))
        disp[:u[0].disp_3d[i].shape[0]] = u[0].disp_3d[i]
        for j in range(1, len(u)):
            disp[u[0].disp_3d[i].shape[0] * j:u[0].disp_3d[i].shape[0] * (j + 1)] = u[j].disp_3d[i]
        joint_disp_3d.append(disp)
    return joint_disp_3d