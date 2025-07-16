import logging
from app.agents.evaluator import create_evaluator_node
from app.agents.executor import create_executor_node
from app.agents.planner import create_planner_node
from app.experts.expert import ExpertBase, ExpertTask
from app.config import settings
from app.experts.prompts.content_prompt import (
    MONICA_PLANNER_SYSTEM_PROMPT, MONICA_PLANNER_TASK_PROMPT,
    MONICA_EXECUTOR_SYSTEM_PROMPT, MONICA_EXECUTOR_TASK_PROMPT,
    MONICA_EVALUATOR_SYSTEM_PROMPT, MONICA_EVALUATOR_TASK_PROMPT
)
from app.types.output import (
    ContentPlannerResult, ContentEvaluatorResult, ContentExecutorResult,
    Platform, MarketingTechnique, PlatformContent
)
from typing import List, Dict, Any


class ContentExpert(ExpertBase):
    """
    Content Generation Expert Monica
    Responsible for generating platform-adapted content based on marketing strategies using various marketing techniques
    """
    
    def __init__(self, index: int = 1):
        super().__init__(f"Monica {index}", f"Monica {index} is a content generation expert specializing in platform-adapted content creation with marketing techniques")
        self.inbox_topic = f"{settings.rocketmq_topic_prefix}_inbox_monica"
        
        # Marketing techniques library
        self.marketing_techniques = self._initialize_marketing_techniques()
        
        # Platform configuration
        self.platform_configs = self._initialize_platform_configs()

    def _initialize_marketing_techniques(self) -> List[MarketingTechnique]:
        """Initialize marketing techniques library"""
        return [
            MarketingTechnique(
                name="Newsjacking",
                professional_term="Newsjacking",
                description="Leverage current trending news/events to attract attention and quickly produce relevant content",
                platform_suitability={
                    Platform.TWITTER: 0.9,
                    Platform.FACEBOOK: 0.7,
                    Platform.REDDIT: 0.6,
                    Platform.LEMON8: 0.5
                },
                content_structure="Trending event + brand association + timely response"
            ),
            MarketingTechnique(
                name="Storytelling",
                professional_term="Storytelling",
                description="Use story plots to trigger emotional resonance and memory reinforcement",
                platform_suitability={
                    Platform.FACEBOOK: 0.9,
                    Platform.LEMON8: 0.8,
                    Platform.REDDIT: 0.7,
                    Platform.TWITTER: 0.6
                },
                content_structure="Story opening + plot development + emotional climax + brand association"
            ),
            MarketingTechnique(
                name="Social Proof",
                professional_term="Social Proof",
                description="Display user reviews, ratings, user counts, etc., to enhance trust",
                platform_suitability={
                    Platform.FACEBOOK: 0.8,
                    Platform.REDDIT: 0.8,
                    Platform.LEMON8: 0.7,
                    Platform.TWITTER: 0.6
                },
                content_structure="User testimonials + data support + trust building"
            ),
            MarketingTechnique(
                name="User-Generated Content",
                professional_term="UGC (User-Generated Content)",
                description="Encourage users to share experiences, comments, and photos",
                platform_suitability={
                    Platform.LEMON8: 0.9,
                    Platform.FACEBOOK: 0.8,
                    Platform.TWITTER: 0.7,
                    Platform.REDDIT: 0.6
                },
                content_structure="User incentives + participation guidance + content display"
            ),
            MarketingTechnique(
                name="How-to Guides",
                professional_term="How-to Guides / Actionable Tips",
                description="Provide actionable advice, operation steps, and practical methods",
                platform_suitability={
                    Platform.REDDIT: 0.9,
                    Platform.LEMON8: 0.8,
                    Platform.FACEBOOK: 0.7,
                    Platform.TWITTER: 0.6
                },
                content_structure="Problem identification + solutions + step-by-step guidance"
            ),
            MarketingTechnique(
                name="Data-driven Content",
                professional_term="Data-driven Content",
                description="Use statistical data, charts, and research results to enhance authority",
                platform_suitability={
                    Platform.REDDIT: 0.8,
                    Platform.FACEBOOK: 0.7,
                    Platform.TWITTER: 0.7,
                    Platform.LEMON8: 0.5
                },
                content_structure="Data display + analysis interpretation + conclusion derivation"
            ),
            MarketingTechnique(
                name="Emotional Triggering",
                professional_term="Emotional Triggering",
                description="Trigger user emotions to drive sharing and participation",
                platform_suitability={
                    Platform.FACEBOOK: 0.8,
                    Platform.LEMON8: 0.8,
                    Platform.TWITTER: 0.7,
                    Platform.REDDIT: 0.6
                },
                content_structure="Emotional hook + emotion escalation + call to action"
            ),
            MarketingTechnique(
                name="Comparison Content",
                professional_term="Comparison Content",
                description="Compare different products/solutions to help decision-making",
                platform_suitability={
                    Platform.REDDIT: 0.8,
                    Platform.FACEBOOK: 0.7,
                    Platform.LEMON8: 0.6,
                    Platform.TWITTER: 0.5
                },
                content_structure="Comparison dimensions + pros/cons analysis + selection advice"
            ),
            MarketingTechnique(
                name="Seasonal Content",
                professional_term="Seasonal/Thematic Content",
                description="Create content around holidays, anniversaries, and social events",
                platform_suitability={
                    Platform.LEMON8: 0.8,
                    Platform.FACEBOOK: 0.8,
                    Platform.TWITTER: 0.7,
                    Platform.REDDIT: 0.5
                },
                content_structure="Holiday atmosphere + brand integration + emotional resonance"
            )
        ]

    def _initialize_platform_configs(self) -> Dict[Platform, Dict[str, Any]]:
        """Initialize platform configurations"""
        return {
            Platform.TWITTER: {
                "character_limit": 280,
                "hashtag_limit": 3,
                "optimal_times": ["09:00-10:00", "18:00-19:00"],
                "content_structure": "钩子 + 核心信息 + 行动号召",
                "engagement_features": ["问题", "投票", "转发鼓励"]
            },
            Platform.FACEBOOK: {
                "character_limit": 5000,
                "recommended_length": "500-1000",
                "optimal_times": ["15:00 周三", "14:00-15:00 周日"],
                "content_structure": "故事开头 + 详细内容 + 社群互动",
                "engagement_features": ["评论引导", "分享鼓励", "投票"]
            },
            Platform.REDDIT: {
                "character_limit": None,
                "content_focus": "价值提供",
                "optimal_times": ["工作日晚上", "周末下午"],
                "content_structure": "价值主张 + 详细分析 + 讨论引导",
                "engagement_features": ["深度讨论", "专业见解", "社区参与"]
            },
            Platform.LEMON8: {
                "character_limit": None,
                "content_focus": "视觉优先",
                "optimal_times": ["19:00-21:00", "周末全天"],
                "content_structure": "视觉吸引 + 生活化内容 + 实用价值",
                "engagement_features": ["美学展示", "生活技巧", "标签优化"]
            }
        }

    async def run(self, task: ExpertTask):
        """Execute content generation task"""
        try:
            # 1. Create content generation plan
            planner_task_prompt = MONICA_PLANNER_TASK_PROMPT.format(
                task_name=task.task_name,
                task_description=task.task_description,
                task_goal=task.task_goal,
                marketing_strategy=getattr(task, 'marketing_strategy', ''),
                target_platforms=getattr(task, 'target_platforms', []),
                content_types=getattr(task, 'content_types', []),
                target_audience=getattr(task, 'target_audience', '')
            )
            
            plan_result: ContentPlannerResult = await self.planner_agent.ainvoke(
                messages=[{"role": "user", "content": planner_task_prompt}]
            )
            
            logging.info(f"Monica generated content plan with {len(plan_result.tasks)} tasks")

            # 2. Execute content generation
            total_tasks = "\n\n".join([
                f"task_name: {task.task_name}\ntask_description: {task.task_description}\ntask_goal: {getattr(task, 'task_goal', '')}"
                for task in plan_result.tasks
            ])

            unfinished_tasks: List[ContentEvaluatorResult] = []
            
            for retry_count in range(self.retries):
                logging.info(f"Monica execution attempt {retry_count + 1}/{self.retries}")
                
                unfinished_tasks_prompt = "\n\n".join([
                    f"task_name: {task.task_name}\ntask_description: {task.task_description}"
                    for task in unfinished_tasks
                ])

                executor_task_prompt = MONICA_EXECUTOR_TASK_PROMPT.format(
                    total_tasks=total_tasks,
                    unfinished_tasks=unfinished_tasks_prompt
                )
                
                executor_result: ContentExecutorResult = await self.executor_agent.ainvoke(
                    messages=[{"role": "user", "content": executor_task_prompt}]
                )
                
                logging.info(f"Monica generated {len(executor_result.generated_content)} content pieces")

                # 3. Evaluate content generation results
                executor_results_prompt = "\n\n".join([
                    f"task_name: {item.task_name}\ntask_description: {item.task_description}\ntask_result: {item.task_result}"
                    for item in executor_result.items
                ])
                
                evaluator_task_prompt = MONICA_EVALUATOR_TASK_PROMPT.format(
                    tasks=total_tasks,
                    results=executor_results_prompt
                )
                
                evaluator_result: ContentEvaluatorResult = await self.evaluator_agent.ainvoke(
                    messages=[{"role": "user", "content": evaluator_task_prompt}]
                )

                # Check if completed
                if len(evaluator_result.unfinished_tasks) == 0:
                    logging.info("Monica content generation completed successfully")
                    
                    # Return final result
                    return {
                        "status": "completed",
                        "plan": plan_result,
                        "execution": executor_result,
                        "evaluation": evaluator_result,
                        "generated_content": executor_result.generated_content,
                        "quality_metrics": evaluator_result.quality_assessment,
                        "performance_metrics": executor_result.performance_metrics
                    }
                else:
                    logging.info(f"Monica has {len(evaluator_result.unfinished_tasks)} unfinished tasks, retrying...")
                    unfinished_tasks = evaluator_result.unfinished_tasks

            # If retries are exhausted and still not completed
            logging.warning("Monica content generation failed after maximum retries")
            return {
                "status": "failed",
                "plan": plan_result,
                "unfinished_tasks": unfinished_tasks,
                "retry_count": self.retries
            }

        except Exception as e:
            logging.error(f"Monica content generation error: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def create_agents(self):
        """Create agent nodes"""
        self.planner_agent = create_planner_node(ContentPlannerResult, MONICA_PLANNER_SYSTEM_PROMPT)
        self.executor_agent = create_executor_node(ContentExecutorResult, MONICA_EXECUTOR_SYSTEM_PROMPT)
        self.evaluator_agent = create_evaluator_node(ContentEvaluatorResult, MONICA_EVALUATOR_SYSTEM_PROMPT)

    def get_marketing_techniques_for_platform(self, platform: Platform) -> List[MarketingTechnique]:
        """Get marketing techniques suitable for specific platform"""
        return [
            technique for technique in self.marketing_techniques
            if technique.platform_suitability.get(platform, 0) >= 0.6
        ]

    def get_platform_config(self, platform: Platform) -> Dict[str, Any]:
        """Get platform configuration"""
        return self.platform_configs.get(platform, {})

    def generate_content_preview(self, content: PlatformContent) -> str:
        """Generate content preview"""
        preview = f"Platform: {content.platform}\n"
        preview += f"Type: {content.content_type}\n"
        if content.title:
            preview += f"Title: {content.title}\n"
        preview += f"Content: {content.content[:100]}{'...' if len(content.content) > 100 else ''}\n"
        preview += f"Hashtags: {', '.join(content.hashtags)}\n"
        preview += f"Character Count: {content.character_count}\n"
        preview += f"Estimated Reach: {content.estimated_reach}\n"
        preview += f"Engagement Prediction: {content.engagement_prediction:.2f}\n"
        return preview

    def validate_content_compliance(self, content: PlatformContent) -> Dict[str, Any]:
        """Validate content compliance (basic check)"""
        platform_config = self.get_platform_config(content.platform)
        issues = []
        
        # Check character limits
        if platform_config.get("character_limit") and content.character_count > platform_config["character_limit"]:
            issues.append(f"Content exceeds character limit: {content.character_count}/{platform_config['character_limit']}")
        
        # Check hashtag count
        if content.platform == Platform.TWITTER and len(content.hashtags) > platform_config.get("hashtag_limit", 3):
            issues.append(f"Too many hashtags: {len(content.hashtags)}/{platform_config['hashtag_limit']}")
        
        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "platform": content.platform,
            "content_type": content.content_type
        } 