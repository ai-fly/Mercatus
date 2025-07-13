from pydantic import BaseModel

class ExpertTask(BaseModel):
    task_name: str
    task_description: str
    task_goal: str


class ExpertBase:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.agent = self.create_agent()
        self.retries = 3
        self.trust_score = 80


    async def run(self, task: ExpertTask):
        raise NotImplementedError("Subclasses must implement this method")

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def create_agent(self):
        raise NotImplementedError("Subclasses must implement this method")


