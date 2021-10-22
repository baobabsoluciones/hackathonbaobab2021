import unittest
from unittest.mock import patch, Mock, MagicMock

# we mock everything that's airflow related:
from cornflow_client import SchemaManager, ApplicationCore
from cornflow_client.airflow.dag_utilities import cf_solve


class BaseDAGTests:
    class SolvingTests(unittest.TestCase):
        def setUp(self) -> None:
            self.app = None
            self.config = {}

        @property
        def app(self) -> ApplicationCore:
            return self._app

        @app.setter
        def app(self, value) -> None:
            self._app = value

        def test_schema_load(self):
            self.assertIsInstance(self.app.instance.schema, dict)
            self.assertIsInstance(self.app.solution.schema, dict)
            self.assertIsInstance(self.app.schema, dict)

        def test_config_requirements(self):
            keys = {"solver", "timeLimit"}
            props = self.app.schema["properties"]
            dif = keys - props.keys()
            self.assertEqual(len(dif), 0)
            self.assertIn("enum", props["solver"])
            self.assertGreater(len(props["solver"]["enum"]), 0)

        def test_try_solving_testcase(self, config=None):
            config = config or self.config
            tests = self.app.test_cases
            for pos, data in enumerate(tests):
                data_out = None
                if isinstance(data, tuple):
                    # sometimes we have input and output
                    data, data_out = data
                marshm = SchemaManager(self.app.instance.schema).jsonschema_to_flask()
                marshm().load(data)
                if data_out is not None:
                    solution_data, log, log_dict = self.app.solve(
                        data, config, data_out
                    )
                else:
                    # for compatibility with previous format
                    solution_data, log, log_dict = self.app.solve(data, config)
                if solution_data is None:
                    raise ValueError("No solution found")
                marshm = SchemaManager(self.app.solution.schema).jsonschema_to_flask()
                marshm().load(solution_data)
                marshm().validate(solution_data)
                self.assertTrue(len(solution_data) > 0)
                instance = self.app.instance.from_dict(data)
                solution = self.app.solution.from_dict(solution_data)
                s = self.app.get_default_solver_name()
                experim = self.app.get_solver(s)(instance, solution)
                experim.check_solution()
                experim.get_objective()

        @patch("cornflow_client.airflow.dag_utilities.connect_to_cornflow")
        def test_complete_solve(self, connectCornflow, config=None):
            config = config or self.config
            tests = self.app.test_cases
            for pos, data in enumerate(tests):
                data_out = None
                if isinstance(data, tuple):
                    # sometimes we have input and output
                    data, data_out = data
                mock = Mock()
                mock.get_data.return_value = dict(data=data, config=config)
                connectCornflow.return_value = mock
                dag_run = Mock()
                dag_run.conf = dict(exec_id="exec_id")
                cf_solve(
                    fun=self.app.solve,
                    dag_name=self.app.name,
                    secrets="",
                    dag_run=dag_run,
                )
                mock.get_data.assert_called_once()
                mock.write_solution.assert_called_once()


class SportsScheduling(BaseDAGTests.SolvingTests):
    def setUp(self):
        super().setUp()
        from hackathonbaobab2021 import SportsScheduling

        self.app = SportsScheduling()
        self.config = dict(solver="default", threads=1, timeLimit=60, msg=False)