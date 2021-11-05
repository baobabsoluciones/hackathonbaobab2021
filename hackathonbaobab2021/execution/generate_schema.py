import json

from hackathonbaobab2021.core import Instance, Experiment
from hackathonbaobab2021.solver import Default
import os


def generate_schema(filename="ITC2021_Test1.xml"):
    directory = os.path.join(os.path.dirname(__file__), "../data/")
    path = os.path.join(directory, filename)
    instance = Instance.from_xml(path)
    schema = instance.generate_schema()
    schema_path = path + "_schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=4, sort_keys=True)
    json_path = path + ".json"
    instance.to_json(json_path)
    instance = Instance.from_json(json_path)
    xml_out_path = path + "_out.xml"
    # instance.to_xml(xml_out_path)
    errors = instance.check_schema()
    experiment = Experiment(instance=instance, solution=None)
    experiment.check_solution()


def generate_instance_solution(filename="ITC2021_Test1.xml"):
    directory = os.path.join(os.path.dirname(__file__), "../data/")
    path = os.path.join(directory, filename)
    instance = Instance.from_xml(path)
    instance.to_json(directory + "example_instance.json")
    experiment = Default(instance=instance, solution=None)
    experiment.solve({})
    experiment.solution.to_json(directory + "example_solution.json")


if __name__ == "__main__":
    # generate_schema()
    generate_instance_solution("TestInstanceDemo.xml")
