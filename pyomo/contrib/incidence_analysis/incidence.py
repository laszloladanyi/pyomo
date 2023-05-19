#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2008-2022
#  National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________
"""Functionality for identifying variables that are incident on expressions

"""
import enum
from pyomo.core.expr.visitor import identify_variables
from pyomo.repn import generate_standard_repn
from pyomo.common.backports import nullcontext
from pyomo.util.subsystems import TemporarySubsystemManager


class IncidenceMethod(enum.Enum):
    identify_variables = 0
    standard_repn = 1


def _get_incident_via_identify_variables(expr, include_fixed):
    # Note that identify_variables will not identify the same variable
    # more than once.
    return list(identify_variables(expr, include_fixed=include_fixed))


def _get_incident_via_standard_repn(expr, include_fixed, linear_only):
    if include_fixed:
        to_unfix = [
            var for var in identify_variables(expr, include_fixed=True)
            if var.fixed
        ]
        context = TemporarySubsystemManager(to_unfix=to_unfix)
    else:
        context = nullcontext()

    with context:
        repn = generate_standard_repn(expr, compute_values=False)

    linear_vars = list(repn.linear_vars)
    if linear_only:
        # TODO: Check coefficients
        return linear_vars
    else:
        variables = repn.linear_vars + repn.quadratic_vars + repn.nonlinear_vars
        unique_variables = []
        id_set = set()
        for var in variables:
            v_id = id(var)
            if v_id not in id_set:
                id_set.add(v_id)
                unique_variables.append(var)
        return unique_variables


def get_incident_variables(
    expr,
    include_fixed=False,
    method=IncidenceMethod.standard_repn,
    #method=IncidenceMethod.identify_variables,
    linear_only=False,
):
    if linear_only and method is IncidenceMethod.identify_variables:
        raise RuntimeError(
            "linear_only=True is not supported when using identify_variables"
        )
    if method is IncidenceMethod.identify_variables:
        return _get_incident_via_identify_variables(expr, include_fixed)
    elif method is IncidenceMethod.standard_repn:
        return _get_incident_via_standard_repn(expr, include_fixed, linear_only)
    else:
        raise ValueError(
            f"Unrecognized value {method} for the method used to identify incident"
            f" variables. Valid options are {IncidenceMethod.identify_variables}"
            f" and {IncidenceMethod.standard_repn}."
        )
