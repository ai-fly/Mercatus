from dataclasses import Field
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, List


class Platform(str, Enum):
    """Supported platform types"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    REDDIT = "reddit"
    LEMON8 = "lemon8"


class ContentType(str, Enum):
    """Content types"""
    TEXT = "text"
    TEXT_IMAGE = "text_image"
    VIDEO = "video"


class Region(str, Enum):
    """Region codes"""
    CHINA = "cn"
    USA = "us"
    UK = "uk"
    EU = "eu"
    VIETNAM = "vn"
    UAE = "ae"
    RUSSIA = "ru"


class ComplianceStatus(str, Enum):
    """Compliance status"""
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MODIFICATION = "needs_modification"


# === Monica (Content Generation Expert) Types ===

class MarketingTechnique(BaseModel):
    """Marketing techniques"""
    name: str = Field(description="Technique name")
    professional_term: str = Field(description="Professional term")
    description: str = Field(description="Technique description")
    platform_suitability: Dict[Platform, float] = Field(description="Platform suitability score (0-1)")
    content_structure: str = Field(description="Content structure recommendations")


class PlatformContent(BaseModel):
    """Platform-adapted content"""
    platform: Platform = Field(description="Target platform")
    content_type: ContentType = Field(description="Content type")
    title: Optional[str] = Field(description="Title", default=None)
    content: str = Field(description="Main content")
    hashtags: List[str] = Field(description="Hashtag list", default_factory=list)
    media_urls: List[str] = Field(description="Media URLs", default_factory=list)
    call_to_action: Optional[str] = Field(description="Call to action", default=None)
    optimal_posting_time: Optional[str] = Field(description="Optimal posting time", default=None)
    character_count: int = Field(description="Character count")
    estimated_reach: int = Field(description="Estimated reach")
    engagement_prediction: float = Field(description="Engagement prediction (0-1)")


class ContentQualityMetrics(BaseModel):
    """Content quality metrics"""
    relevance_score: float = Field(description="Relevance score (0-1)")
    engagement_potential: float = Field(description="Engagement potential (0-1)")
    brand_alignment: float = Field(description="Brand alignment (0-1)")
    platform_optimization: float = Field(description="Platform optimization (0-1)")
    overall_quality: float = Field(description="Overall quality (0-1)")


class ContentGenerationStrategy(BaseModel):
    """Content generation strategy"""
    target_audience: str = Field(description="Target audience")
    key_message: str = Field(description="Key message")
    marketing_techniques: List[MarketingTechnique] = Field(description="Marketing techniques used")
    tone_of_voice: str = Field(description="Tone of voice")
    content_calendar_suggestion: str = Field(description="Content calendar suggestions")


class MonicaResult(BaseModel):
    """Monica content generation result"""
    strategy: ContentGenerationStrategy = Field(description="Generation strategy")
    platform_contents: List[PlatformContent] = Field(description="Platform-adapted content")
    quality_metrics: ContentQualityMetrics = Field(description="Quality metrics")
    performance_prediction: Dict[str, float] = Field(description="Performance prediction")
    content_variations: List[str] = Field(description="Content variations", default_factory=list)
    optimization_suggestions: List[str] = Field(description="Optimization suggestions", default_factory=list)


# === Henry (Content Review Expert) Types ===

class PolicyViolation(BaseModel):
    """Policy violation"""
    policy_name: str = Field(description="Policy name")
    violation_type: str = Field(description="Violation type")
    description: str = Field(description="Violation description")
    severity: str = Field(description="Severity level: low, medium, high")
    recommendation: str = Field(description="Modification recommendation")


class PlatformComplianceResult(BaseModel):
    """Platform compliance check result"""
    platform: Platform = Field(description="Platform")
    status: ComplianceStatus = Field(description="Compliance status")
    violations: List[PolicyViolation] = Field(description="Violations", default_factory=list)
    policy_version: str = Field(description="Policy version")
    last_updated: str = Field(description="Last updated time")
    compliance_score: float = Field(description="Compliance score (0-1)")


class RegionalComplianceResult(BaseModel):
    """Regional compliance check result"""
    region: Region = Field(description="Region")
    status: ComplianceStatus = Field(description="Compliance status")
    legal_requirements: List[str] = Field(description="Legal requirements", default_factory=list)
    prohibited_content: List[str] = Field(description="Prohibited content", default_factory=list)
    mandatory_disclosures: List[str] = Field(description="Mandatory disclosures", default_factory=list)
    risk_assessment: str = Field(description="Risk assessment")
    compliance_score: float = Field(description="Compliance score (0-1)")


class ContentAnalysis(BaseModel):
    """Content analysis result"""
    language_detected: str = Field(description="Detected language")
    sensitive_topics: List[str] = Field(description="Sensitive topics", default_factory=list)
    sentiment_analysis: str = Field(description="Sentiment analysis")
    content_category: str = Field(description="Content category")
    risk_factors: List[str] = Field(description="Risk factors", default_factory=list)
    content_quality: float = Field(description="Content quality (0-1)")


class HenryResult(BaseModel):
    """Henry content review result"""
    overall_status: ComplianceStatus = Field(description="Overall status")
    content_analysis: ContentAnalysis = Field(description="Content analysis")
    platform_compliance: List[PlatformComplianceResult] = Field(description="Platform compliance results")
    regional_compliance: List[RegionalComplianceResult] = Field(description="Regional compliance results")
    overall_risk_score: float = Field(description="Overall risk score (0-1)")
    recommendations: List[str] = Field(description="Modification recommendations", default_factory=list)
    approval_conditions: List[str] = Field(description="Approval conditions", default_factory=list)
    review_notes: str = Field(description="Review notes")


# === Expert Communication Types ===

class ExpertMessage(BaseModel):
    """Expert communication message"""
    from_expert: str = Field(description="Sender expert")
    to_expert: str = Field(description="Receiver expert")
    message_type: str = Field(description="Message type")
    content: Dict = Field(description="Message content")
    timestamp: str = Field(description="Timestamp")
    priority: str = Field(description="Priority: low, medium, high")


class TaskFailureReport(BaseModel):
    """Task failure report"""
    task_id: str = Field(description="Task ID")
    failure_count: int = Field(description="Failure count")
    failure_reasons: List[str] = Field(description="Failure reasons")
    last_error: str = Field(description="Last error")
    suggested_actions: List[str] = Field(description="Suggested actions")


# === Base Agent Types ===

class AgentPlannerResultItem(BaseModel):
    """
    Specific single task information
    """
    task_name: str = Field(description="The name of the task")
    task_description: str = Field(description="The description of the task")


class AgentPlannerResult(BaseModel):
    """
    Based on user input, generate a plan to guide AI in executing tasks, consisting of multiple tasks.
    """
    tasks: list[AgentPlannerResultItem] = Field(description="The tasks of the plan")


class AgentEvaluatorResult(BaseModel):
    """
    Evaluate executor agent's execution result
    """
    unfinished_tasks: list[AgentPlannerResultItem] = Field(description="The tasks that are not finished")


class AgentExecutorResultItem(BaseModel):
    """
    The result of a single task execution
    """
    task_name: str = Field(description="The name of the task")
    task_description: str = Field(description="The description of the task")
    task_result: str = Field(description="The result of the execution")


class AgentExecutorResult(BaseModel):
    """
    The result of the execution of a plan, consisting of multiple tasks.
    """
    items: list[AgentExecutorResultItem] = Field(description="The items of the execution")


# === Monica Specific Agent Types ===

class MonicaPlannerResult(AgentPlannerResult):
    """Monica content generation plan result"""
    content_strategy: ContentGenerationStrategy = Field(description="Content strategy")
    target_platforms: List[Platform] = Field(description="Target platforms")
    content_types: List[ContentType] = Field(description="Content types")


class MonicaEvaluatorResult(AgentEvaluatorResult):
    """Monica content generation evaluation result"""
    quality_assessment: ContentQualityMetrics = Field(description="Quality assessment")
    improvement_suggestions: List[str] = Field(description="Improvement suggestions", default_factory=list)


class MonicaExecutorResult(AgentExecutorResult):
    """Monica content generation execution result"""
    generated_content: List[PlatformContent] = Field(description="Generated content")
    performance_metrics: Dict[str, float] = Field(description="Performance metrics")


# === Henry Specific Agent Types ===

class HenryPlannerResult(AgentPlannerResult):
    """Henry content review plan result"""
    review_criteria: List[str] = Field(description="Review criteria")
    target_platforms: List[Platform] = Field(description="Target platforms")
    target_regions: List[Region] = Field(description="Target regions")


class HenryEvaluatorResult(AgentEvaluatorResult):
    """Henry content review evaluation result"""
    compliance_assessment: Dict[str, float] = Field(description="Compliance assessment")
    risk_evaluation: str = Field(description="Risk evaluation")


class HenryExecutorResult(AgentExecutorResult):
    """Henry content review execution result"""
    review_results: List[HenryResult] = Field(description="Review results")
    final_decision: ComplianceStatus = Field(description="Final decision")
