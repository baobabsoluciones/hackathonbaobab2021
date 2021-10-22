import json

from hackathonbaobab2021.core import Instance, Experiment
import os


def generate_schema():
    path = os.path.join(os.path.dirname(__file__), "../data/ITC2021_Test1.xml")
    instance = Instance.from_xml(path)
    schema = instance.generate_schema()
    schema_path = path + "_schema.json"
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=4, sort_keys=True)
    json_path = path + ".json"
    instance.to_json(json_path)
    instance = Instance.from_json(json_path)
    errors = instance.check_schema()
    experiment = Experiment(instance=instance, solution=None)
    experiment.check_solution()


if __name__ == "__main__":
    generate_schema()
