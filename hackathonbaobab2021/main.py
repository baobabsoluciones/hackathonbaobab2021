import click
import execution.run_batch as rb
import os
import ast
import json


class PythonLiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)


class PythonJsonOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return json.loads(value)
        except:
            raise click.BadParameter(value)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--directory", default=".", help="data where the input data zip files are."
)
@click.option(
    "--scenarios",
    default="[]",
    cls=PythonLiteralOption,
    help="list of scenario to solve.",
)
@click.option("--scenario", default=None, help="list of scenario to solve.")
@click.option(
    "--instances",
    default="[]",
    cls=PythonLiteralOption,
    help="list of instances to solve.",
)
@click.option(
    "--instance",
    default=None,
    help="In order to solve only one instance scenario/instance.",
)
@click.option("--solver", default="default", help="solver to use.")
@click.option(
    "--test/--no-test",
    default=True,
    help="if given only solves 3 instances of each scenario.",
)
@click.option(
    "--zip/--no-zip",
    default=False,
    help="if given it zips all the results into one file.",
)
@click.option(
    "--options", default="{}", cls=PythonJsonOption, help="Options to pass to solver."
)
def solve_scenarios(
    directory, scenarios, scenario, solver, test, instances, instance, zip, options
):
    """Solves a batch of instances inside a zip with a solver and zips the results"""
    # print(scenarios)
    # print(test)
    if not len(instances):
        instances = None
    if instance is not None:
        instances = [instance]
    if scenario is not None:
        scenarios = [scenario]
    rb.solve_scenarios_and_zip(
        scenarios,
        os.path.join(directory, solver),
        solver,
        test=test,
        instances=instances,
        zip=zip,
        options=options,
    )


@cli.command()
@click.option("--path", default="default", help="the path to the zipfile to analyse.")
@click.option("--path_out", help="the path for the output csv.")
def export_table(path, path_out):
    """Reads a result zip and exports the table in a csv"""
    table = rb.get_table(path)
    table.to_csv(path_out, index=False)
    return


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    cli()
