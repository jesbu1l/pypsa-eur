# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: : 2020-2024 The PyPSA-Eur Authors
#
# SPDX-License-Identifier: MIT
"""
Build industrial energy demand per model region.
"""

import pandas as pd
from _helpers import set_scenario_config

if __name__ == "__main__":
    if "snakemake" not in globals():
        from _helpers import mock_snakemake

        snakemake = mock_snakemake(
            "build_industrial_energy_demand_per_node",
            simpl="",
            clusters=20,
            planning_horizons=2050,
        )
    set_scenario_config(snakemake)

    # import ratios
    fn = snakemake.input.industry_sector_ratios
    sector_ratios = pd.read_csv(fn, header=[0, 1], index_col=0)

    # material demand per node and industry (Mton/a)
    fn = snakemake.input.industrial_production_per_node
    nodal_production = pd.read_csv(fn, index_col=0) / 1e3

    # energy demand today to get current electricity
    fn = snakemake.input.industrial_energy_demand_per_node_today
    nodal_today = pd.read_csv(fn, index_col=0)

    nodal_sector_ratios = pd.concat(
        {node: sector_ratios[node[:2]] for node in nodal_production.index}, axis=1
    )

    nodal_production_stacked = nodal_production.stack()
    nodal_production_stacked.index.names = [None, None]
    # sector: should be electric arc, steelworks etc etc.
    # final energy consumption per node, sector and carrier
    index = pd.MultiIndex.from_product(
        [nodal_production.index, nodal_production.columns], names=("node", "sector")
    )
    nodal_df = nodal_sector_ratios.multiply(nodal_production_stacked).T

    # nodal_dict = {k: s * sector_ratios for k, s in nodal_production.iterrows()}
    # nodal_df = pd.concat(nodal_dict, axis=1).T
    # TODO: Merge conflict
    # nodal_df = (
    #     (nodal_sector_ratios.multiply(nodal_production_stacked))
    #     .T.groupby(level=0)
    #     .sum()
    # )

    rename_sectors = {
        "elec": "electricity",
        "biomass": "solid biomass",
        "heat": "low-temperature heat",
    }
    nodal_df.rename(columns=rename_sectors, inplace=True)

    nodal_df.index.set_names(["node", "sector"], inplace=True)
    nodal_df.index.name = "TWh/a (MtCO2/a)"

    fn = snakemake.output.industrial_energy_demand_per_node
    nodal_df.to_csv(fn, float_format="%.2f")
