from dataclasses import Field
from enum import Enum
from typing import Any, Set, Type, List
import uuid

from pydantic import BaseModel
from app.clients.redis_client import redis_client_instance
from app.experts.expert import ExpertBase


class TeamMember(BaseModel):
    expert: Type[ExpertBase] = Field(description="The expert of the team member")
    member_count: int = Field(description="The number of team members")


class TeamGoal(BaseModel):
    team_goal: str = Field(description="The goal of the team")
    goal_description: str = Field(description="The description of the team goal")
    team_members: Set[TeamMember] = Field(description="The members of the team")



class BlackboardValue(BaseModel):
    expert_name: str = Field(description="The name of the expert")
    stage: str = Field(description="The stage of the expert")

class BlackboardStage(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    FINISHED = "finished"

class Blackboard():
    """
    The blackboard is a shared memory for the team.
    """
    def __init__(self, team_id: str, team_goal: TeamGoal):
        self.team_id = team_id
        self.team_goal = team_goal
        self.blackboard = {}
        
    def get_blackboard(self, expert_name: str, stage: BlackboardStage) -> BlackboardValue:
        key = self.build_key(expert_name, stage)
        value = redis_client_instance.get_redis_client().get(key)
        if value:
            return BlackboardValue.model_validate_json(value)
        return None
    
    def set_blackboard(self, expert_name: str, stage: BlackboardStage, value: BlackboardValue):
        key = self.build_key(expert_name, stage)
        redis_client_instance.get_redis_client().lpush(key, value.model_dump_json())


    def build_key(self, expert_name: str, stage: BlackboardStage) -> str:
        return f"BLACKBOARD:{self.team_id}:{stage.value}:{expert_name}"
    
class Team:

    def __init__(self, team_goal: TeamGoal):
        self.team_goal = team_goal
        self.init_experts()
        self.blackboard = Blackboard(f"team_{uuid.uuid4()}")

    def start(self):
        pass

        
    def init_experts(self):
        self.experts = {}
        for member in self.team_goal.team_members:
            expert_type = member.expert
            clones = [
                expert_type(i + 1)
                for i in range(member.member_count)
            ]
            self.experts[expert_type] = clones

    def get_experts(self, expert_type: Type[ExpertBase]) -> List[ExpertBase]:
        return self.experts[expert_type]
