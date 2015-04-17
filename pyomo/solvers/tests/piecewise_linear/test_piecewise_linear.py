#  _________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2014 Sandia Corporation.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  This software is distributed under the BSD License.
#  _________________________________________________________________________

import os
from os.path import dirname, abspath, join
thisDir = dirname( abspath(__file__) )

import pyutilib.th as unittest
import pyutilib.misc

import pyomo.opt
from pyomo.core.base import Var
from pyomo.core.base.objective import minimize, maximize
from pyomo.core.base.piecewise import Bound, PWRepn
from pyomo.solvers.tests.io.writer_test_cases import testCases

yaml_available=False
try:
    import yaml
    yaml_available = True
except:
    pass

smoke_problems = ['convex_var','step_var','step_vararray']

nightly_problems = ['convex_vararray', 'concave_vararray', \
                'concave_var','piecewise_var', 'piecewise_vararray']

expensive_problems = ['piecewise_multi_vararray', \
                'convex_multi_vararray1','concave_multi_vararray1', \
                'convex_multi_vararray2','concave_multi_vararray2']


testing_solvers = {}
#testing_solvers['cplex','lp'] = False
testing_solvers['cplexamp','nl'] = False
#testing_solvers['ipopt','nl'] = False
#testing_solvers['cplex','python'] = False
#testing_solvers['_cplex_persistent','python'] = False
testCases_copy = list(testCases)
#testCases_copy.append( SolverTestCase(name='_cplex_persistent',
#                                 io='python'))
for test_case in testCases_copy:
    if ((test_case.name,test_case.io) in testing_solvers) and \
       (test_case.available):
        testing_solvers[(test_case.name,test_case.io)] = True

def createTestMethod(pName,problem,solver,writer,kwds):

    def testMethod(obj):

        m = pyutilib.misc.import_file(os.path.join(thisDir,
                                                   'problems',
                                                   problem),
                                      clear_cache=True)

        model = m.define_model(**kwds)

        # Generates canonical repn for those writers that need it
        if writer != 'nl':
            model.preprocess()

        opt = pyomo.opt.SolverFactory(solver,solver_io=writer)
        results = opt.solve(model)
        model.load(results)

        # non-recursive
        new_results = ((var.cname(),var.value) for var in model.component_data_objects(Var, active=True))
        baseline_results = getattr(obj,problem+'_results')
        for name, value in new_results:
            if abs(baseline_results[name]-value) > 0.00001:
                raise IOError("Difference in baseline solution values and "
                              "current solution values using:\n" + \
                "Solver: "+solver+"\n" + \
                "Writer: "+writer+"\n" + \
                "Variable: "+name+"\n" + \
                "Solution: "+str(value)+"\n" + \
                "Baseline: "+str(baseline_results[name])+"\n")

    return testMethod

def assignTests(cls, problem_list):
    for solver,writer in testing_solvers:
        for PROBLEM in problem_list:
            aux_list = ['','force_pw']
            for AUX in aux_list:
                for REPN in PWRepn:
                    for BOUND_TYPE in Bound:
                        for SENSE in [maximize,minimize]:
                            if not( ((BOUND_TYPE == Bound.Lower) and (SENSE == maximize)) or \
                                    ((BOUND_TYPE == Bound.Upper) and (SENSE == minimize)) or \
                                    ((REPN in [PWRepn.BIGM_BIN,PWRepn.BIGM_SOS1,PWRepn.MC]) and ('step' in PROBLEM)) ):
                                kwds = {}
                                kwds['sense'] = SENSE
                                kwds['pw_repn'] = REPN
                                kwds['pw_constr_type'] = BOUND_TYPE
                                if SENSE == maximize:
                                    attrName = "test_{0}_{1}_{2}_{3}_{4}_{5}".format(PROBLEM,REPN,BOUND_TYPE,'maximize',solver,writer)
                                elif SENSE == minimize:
                                    attrName = "test_{0}_{1}_{2}_{3}_{4}_{5}".format(PROBLEM,REPN,BOUND_TYPE,'minimize',solver,writer)
                                if AUX != '':
                                    kwds[AUX] = True
                                    attrName += '_'+AUX
                                setattr(cls,attrName,createTestMethod(attrName,PROBLEM,solver,writer,kwds))
                                if yaml_available:
                                    with open(join(thisDir,'baselines',PROBLEM+'_baseline_results.yml'),'r') as f:
                                        baseline_results = yaml.load(f)
                                        setattr(cls,PROBLEM+'_results',baseline_results)

@unittest.skipUnless(yaml_available, "PyYAML module is not available.")
class PW_Tests(unittest.TestCase): pass

@unittest.category('nightly', 'expensive')
class PiecewiseLinearTest_Nightly(PW_Tests): pass
assignTests(PiecewiseLinearTest_Nightly, nightly_problems)

@unittest.category('smoke', 'nightly', 'expensive')
class PiecewiseLinearTest_Smoke(PW_Tests): pass
assignTests(PiecewiseLinearTest_Smoke, smoke_problems)

@unittest.category('expensive')
class PiecewiseLinearTest_Expensive(PW_Tests): pass
assignTests(PiecewiseLinearTest_Expensive, expensive_problems)

if __name__ == "__main__":
    unittest.main()

