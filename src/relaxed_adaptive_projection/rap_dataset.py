# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0
import os
import numpy as np
import pandas as pd
import json
import itertools
from functools import reduce

class RAPDataset:
    def __init__(self, df, domain):
        self.df = df
        self.domain = domain

    def get_dataset(self):

        # return one-hot encoding of entrire dataset
        dataset = self.project_feats()

        self.n, self.d = dataset.shape
        return dataset

    def gen_synthetic(self, N):
        """
        Generate synthetic data conforming to the given features
        N: the number of individuals
        """
        synth_D = np.hstack(
            [
                (
                    np.random.randint(low=0, high=n, size=N)[:, None] == np.arange(n)
                ).astype(np.float)
                for n in self.domain.values()
            ]
        )

        return synth_D

    def preprocess(self, dataset):
        return dataset

    def postprocess(self, dataset):
        return dataset

    def _get_size_domain(self, proj):

        return reduce(lambda x, y: x * y, [self.domain[feat] for feat in proj], 1)

    def randomKway(self, num_kways=24, k=3, seed=0):
        """
        return num_kways k-way tuples from data features
        """

        prng = np.random.RandomState(seed)
        total = self.df.shape[0]

        # generate k-ways with support smaller than the actual population
        proj = [
            p
            for p in itertools.combinations(self.df.columns, k)
            if self._get_size_domain(p) <= total
        ]

        # randomly select subset from k-ways of size num_kways
        if len(proj) > num_kways:
            proj = [proj[i] for i in prng.choice(len(proj), num_kways, replace=False)]

        return proj

    def get_queries(self, feats, N=None):
        """
        get N queries from marginals (if N is None, return all queries)
        """

        col_map = {}
        for i, col in enumerate(self.domain.keys()):
            col_map[col] = i

        feat_pos = []
        cur = 0
        for f, sz in enumerate(self.domain.values()):
            feat_pos.append(list(range(cur, cur + sz)))
            cur += sz

        queries = []

        if N is None:
            ## output |feats| tuples of coordinate ranges if we want to enumerate all queries
            for feat in feats:
                queries.append([feat_pos[col_map[col]] for col in feat])

            num_queries = sum(
                [reduce(lambda x, y: x * y, [len(i) for i in q], 1) for q in queries]
            )

            return queries, num_queries

        for feat in feats:
            positions = []
            for col in feat:
                i = col_map[col]
                positions.append(feat_pos[i])
            for tup in itertools.product(*positions):
                queries.append(tup)

        num_queries = len(queries) if N == -1 else N

        return np.array(queries, np.int)[:num_queries], num_queries

    def project_feats(self, feats=None):
        """
        return subset of data over feats
        """

        if feats is None:
            feats = self.domain

        feats_domain = {key: self.domain[key] for key in feats}

        # get binning of attributes
        bins_size_array = [
            (size_bin, np.digitize(self.df[col], range(size_bin + 1), right=True))
            for col, size_bin in feats_domain.items()
        ]

        # perform one-hot-encoding of all features and stack them into a numpy matrix
        bin_dataset = np.hstack(
            [np.eye(size_bin)[bin_array] for size_bin, bin_array in bins_size_array]
        )

        return bin_dataset
