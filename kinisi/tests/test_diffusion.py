"""
Tests for diffusion module

Copyright (c) Andrew R. McCluskey and Benjamin J. Morgan

Distributed under the terms of the MIT License

@author: Andrew R. McCluskey
"""

# pylint: disable=R0201

import unittest
import numpy as np
from numpy.testing import assert_equal
from scipy.stats import norm
from kinisi import diffusion
from uravu.distribution import Distribution


dt = np.linspace(5, 50, 10)
msd = np.linspace(5, 50, 10)
MSD = []
for i in msd:
    MSD.append(Distribution(norm.rvs(loc=i, scale=i * 0.1, size=5000, random_state=np.random.RandomState(1))))


class TestMsd(unittest.TestCase):
    """
    Unit tests for diffusion module
    """

    def test_msd_bootstrap_a(self):
        """
        Test msd_bootstrap for initial normal.
        """
        ordinate = np.random.randn(100, 50, 3)
        to_resample = [
            np.array(ordinate) for i in range(1, 6)
        ]
        boot = diffusion.MSDBootstrap(
            np.linspace(100, 600, 5, dtype=int),
            to_resample,
            progress=False,
            n_resamples=100,
            max_resamples=1000)
        assert_equal(boot.dt.size, 5)
        assert_equal(boot.msd.size, 5)

    def test_msd_bootstrap_b(self):
        """
        Test msd_bootstrap for initial uniform with progress.
        """
        ordinate = np.random.uniform(size=(100, 50, 3))
        to_resample = [
            np.array(ordinate) for i in range(1, 6)
        ]
        boot = diffusion.MSDBootstrap(
            np.linspace(100, 600, 5, dtype=int),
            to_resample,
            progress=True,
            n_resamples=1,
            max_resamples=1000)
        assert_equal(boot.dt.size, 5)
        assert_equal(boot.msd.size, 5)

    def test_msd_bootstrap_c(self):
        """
        Test msd_bootstrap for to go over the limit point.
        """
        ordinate1 = np.random.randn(5, 500, 3)
        ordinate2 = np.random.randn(5, 450, 3)
        ordinate3 = np.random.randn(5, 400, 3)
        ordinate4 = np.random.randn(5, 100, 3)
        ordinate5 = np.random.randn(5, 10, 3)
        to_resample = [
            ordinate1,
            ordinate2,
            ordinate3,
            ordinate4,
            ordinate5,
        ]
        boot = diffusion.MSDBootstrap(
            np.linspace(100, 600, 5, dtype=int),
            to_resample,
            progress=False,
            n_resamples=1,
            max_resamples=10,
            sub_sample_dt=2)
        assert_equal(boot.dt.size, 3)
        assert_equal(boot.msd.size, 3)

