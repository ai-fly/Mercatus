import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.agents.evaluator import create_evaluator_node
from app.agents.executor import create_executor_node
from app.agents.planner import create_planner_node
from app.experts.expert import ExpertBase, ExpertTask
from app.config import settings
from app.experts.prompts.henry_prompt import (
    HENRY_PLANNER_SYSTEM_PROMPT, HENRY_PLANNER_TASK_PROMPT,
    HENRY_EXECUTOR_SYSTEM_PROMPT, HENRY_EXECUTOR_TASK_PROMPT,
    HENRY_EVALUATOR_SYSTEM_PROMPT, HENRY_EVALUATOR_TASK_PROMPT
)
from app.types.output import (
    HenryPlannerResult, HenryEvaluatorResult, HenryExecutorResult,
    Platform, Region, ComplianceStatus, PolicyViolation,
    PlatformComplianceResult, RegionalComplianceResult,
    ContentAnalysis
)


class HenryExpert(ExpertBase):
    """
    Content Review Expert Henry
    Responsible for content compliance checking, platform policy validation, and regional law review
    """
    
    def __init__(self):
        super().__init__("Henry", "Henry is a content review expert specializing in compliance checking and regional law validation")
        self.inbox_topic = f"{settings.rocketmq_topic_prefix}_inbox_henry"
        
        # Platform policy configuration
        self.platform_policies = self._initialize_platform_policies()
        
        # Regional law configuration
        self.regional_laws = self._initialize_regional_laws()
        
        # Risk assessment weights
        self.risk_weights = {
            "platform_policy": 0.3,
            "regional_law": 0.4,
            "content_quality": 0.2,
            "commercial_disclosure": 0.1
        }

    def _initialize_platform_policies(self) -> Dict[Platform, Dict[str, Any]]:
        """Initialize platform policy configuration"""
        return {
            Platform.TWITTER: {
                "policy_url": "https://help.twitter.com/en/rules-and-policies",
                "content_policy": "https://help.twitter.com/en/rules-and-policies/twitter-rules",
                "advertising_policy": "https://business.twitter.com/en/help/ads-policies.html",
                "prohibited_content": [
                    "仇恨言论", "暴力威胁", "误导信息", "版权侵权",
                    "成人内容", "恶意软件", "垃圾信息", "虚假身份"
                ],
                "advertising_requirements": [
                    "付费推广标识 (#ad, #sponsored)",
                    "避免夸大宣传",
                    "年龄适宜性检查",
                    "禁止违禁品广告"
                ],
                "technical_requirements": [
                    "280字符限制",
                    "链接安全检查",
                    "适当标签使用"
                ]
            },
            Platform.FACEBOOK: {
                "policy_url": "https://www.facebook.com/communitystandards",
                "content_policy": "https://www.facebook.com/communitystandards",
                "advertising_policy": "https://www.facebook.com/policies/ads",
                "prohibited_content": [
                    "仇恨言论", "暴力内容", "成人内容", "危险组织",
                    "欺凌骚扰", "虚假信息", "知识产权侵权", "垃圾内容"
                ],
                "advertising_requirements": [
                    "个人健康声明限制",
                    "金融服务合规",
                    "政治广告标识",
                    "酒精赌博限制"
                ],
                "community_standards": [
                    "真实身份要求",
                    "尊重他人隐私",
                    "建设性互动",
                    "原创内容鼓励"
                ]
            },
            Platform.REDDIT: {
                "policy_url": "https://www.redditinc.com/policies/content-policy",
                "content_policy": "https://www.redditinc.com/policies/content-policy",
                "advertising_policy": "https://www.redditinc.com/policies/advertising-policy",
                "prohibited_content": [
                    "骚扰威胁", "暴力内容", "成人内容", "个人信息泄露",
                    "垃圾内容", "投票操纵", "虚假信息", "版权侵权"
                ],
                "community_requirements": [
                    "遵守subreddit规则",
                    "避免过度自我推广",
                    "透明披露商业关系",
                    "提供真实价值"
                ],
                "transparency_requirements": [
                    "利益冲突披露",
                    "付费内容标识",
                    "机器人行为标识"
                ]
            },
            Platform.LEMON8: {
                "policy_url": "https://www.lemon8-app.com/legal/community-guidelines",
                "content_policy": "https://www.lemon8-app.com/legal/community-guidelines",
                "advertising_policy": "https://www.lemon8-app.com/legal/advertising-policy",
                "prohibited_content": [
                    "低质量内容", "误导信息", "版权侵权", "成人内容",
                    "仇恨言论", "暴力内容", "垃圾信息", "虚假评价"
                ],
                "quality_requirements": [
                    "高质量视觉内容",
                    "原创性要求",
                    "实用价值提供",
                    "积极社区互动"
                ],
                "commercial_requirements": [
                    "商业合作标识",
                    "真实体验分享",
                    "避免虚假宣传"
                ]
            }
        }

    def _initialize_regional_laws(self) -> Dict[Region, Dict[str, Any]]:
        """Initialize regional law configuration"""
        return {
            Region.CHINA: {
                "basic_requirements": [
                    "实名制要求",
                    "AI生成内容标记",
                    "信息来源标注",
                    "时效性验证"
                ],
                "prohibited_content": [
                    "政治敏感内容",
                    "危害国家安全",
                    "民族歧视",
                    "虚假信息",
                    "暴力恐怖",
                    "色情内容",
                    "赌博毒品"
                ],
                "special_requirements": [
                    "新闻信息许可",
                    "军事内容管制",
                    "宗教活动限制",
                    "敏感历史话题"
                ],
                "regulatory_framework": [
                    "网络安全法",
                    "数据安全法",
                    "个人信息保护法",
                    "网络信息内容生态治理规定"
                ]
            },
            Region.USA: {
                "basic_requirements": [
                    "FTC广告披露",
                    "真实性要求",
                    "证据支持",
                    "儿童保护"
                ],
                "prohibited_content": [
                    "虚假广告",
                    "误导声明",
                    "版权侵权",
                    "儿童不适宜内容"
                ],
                "ftc_requirements": [
                    "明确标识付费内容",
                    "避免虚假声明",
                    "声明需有证据支持",
                    "儿童隐私保护"
                ],
                "copyright_law": [
                    "DMCA合规",
                    "公平使用原则",
                    "授权使用",
                    "原创内容标记"
                ]
            },
            Region.EU: {
                "basic_requirements": [
                    "GDPR数据保护",
                    "DSA透明度",
                    "广告标识",
                    "消费者保护"
                ],
                "prohibited_content": [
                    "仇恨言论",
                    "虚假广告",
                    "误导信息",
                    "非法内容"
                ],
                "gdpr_requirements": [
                    "用户同意",
                    "数据处理合法性",
                    "用户权利保护",
                    "数据安全措施"
                ],
                "dsa_requirements": [
                    "内容审核透明度",
                    "风险评估",
                    "用户申诉机制",
                    "监管合作"
                ]
            },
            Region.UK: {
                "basic_requirements": [
                    "Online Safety Act合规",
                    "广告标准",
                    "消费者保护",
                    "数据保护"
                ],
                "prohibited_content": [
                    "有害内容",
                    "虚假广告",
                    "仇恨言论",
                    "非法内容"
                ],
                "online_safety_act": [
                    "注意义务",
                    "用户安全",
                    "内容审核",
                    "透明度报告"
                ]
            },
            Region.VIETNAM: {
                "basic_requirements": [
                    "实名验证",
                    "数据本地化",
                    "内容审查配合",
                    "政府监管配合"
                ],
                "prohibited_content": [
                    "政治异议",
                    "社会不稳定",
                    "虚假信息",
                    "违法内容"
                ],
                "decree_147": [
                    "社交平台实名",
                    "24小时删除违法内容",
                    "政府配合义务"
                ]
            },
            Region.UAE: {
                "basic_requirements": [
                    "媒体许可",
                    "内容标准遵守",
                    "文化敏感性",
                    "商业透明度"
                ],
                "prohibited_content": [
                    "道德违规",
                    "安全威胁",
                    "误导内容",
                    "文化不敏感"
                ],
                "media_law": [
                    "自媒体许可",
                    "20项内容标准",
                    "影响者规范"
                ]
            },
            Region.RUSSIA: {
                "basic_requirements": [
                    "外国代理人标签",
                    "内容审计",
                    "政府配合",
                    "数据本地化"
                ],
                "prohibited_content": [
                    "政府批评",
                    "假新闻",
                    "极端主义",
                    "外国影响"
                ],
                "foreign_agent_law": [
                    "境外资金申报",
                    "代理人标签",
                    "定期审计",
                    "活动限制"
                ]
            }
        }

    async def run(self, task: ExpertTask):
        """Execute content review task"""
        try:
            # 1. 制定内容审查计划
            planner_task_prompt = HENRY_PLANNER_TASK_PROMPT.format(
                task_name=task.task_name,
                task_description=task.task_description,
                task_goal=task.task_goal,
                content_to_review=getattr(task, 'content_to_review', ''),
                target_platforms=getattr(task, 'target_platforms', []),
                target_regions=getattr(task, 'target_regions', []),
                content_types=getattr(task, 'content_types', [])
            )
            
            plan_result: HenryPlannerResult = await self.planner_agent.ainvoke(
                messages=[{"role": "user", "content": planner_task_prompt}]
            )
            
            logging.info(f"Henry generated review plan with {len(plan_result.tasks)} tasks")

            # 2. 执行内容审查
            total_tasks = "\n\n".join([
                f"task_name: {task.task_name}\ntask_description: {task.task_description}\ntask_goal: {getattr(task, 'task_goal', '')}"
                for task in plan_result.tasks
            ])

            unfinished_tasks: List[HenryEvaluatorResult] = []
            
            for retry_count in range(self.retries):
                logging.info(f"Henry review attempt {retry_count + 1}/{self.retries}")
                
                unfinished_tasks_prompt = "\n\n".join([
                    f"task_name: {task.task_name}\ntask_description: {task.task_description}"
                    for task in unfinished_tasks
                ])

                executor_task_prompt = HENRY_EXECUTOR_TASK_PROMPT.format(
                    total_tasks=total_tasks,
                    unfinished_tasks=unfinished_tasks_prompt
                )
                
                executor_result: HenryExecutorResult = await self.executor_agent.ainvoke(
                    messages=[{"role": "user", "content": executor_task_prompt}]
                )
                
                logging.info(f"Henry completed review with decision: {executor_result.final_decision}")

                # 3. 评估审查结果
                executor_results_prompt = "\n\n".join([
                    f"task_name: {item.task_name}\ntask_description: {item.task_description}\ntask_result: {item.task_result}"
                    for item in executor_result.items
                ])
                
                evaluator_task_prompt = HENRY_EVALUATOR_TASK_PROMPT.format(
                    tasks=total_tasks,
                    results=executor_results_prompt
                )
                
                evaluator_result: HenryEvaluatorResult = await self.evaluator_agent.ainvoke(
                    messages=[{"role": "user", "content": evaluator_task_prompt}]
                )

                # 检查是否完成
                if len(evaluator_result.unfinished_tasks) == 0:
                    logging.info("Henry content review completed successfully")
                    
                    # 返回最终结果
                    return {
                        "status": "completed",
                        "plan": plan_result,
                        "execution": executor_result,
                        "evaluation": evaluator_result,
                        "review_results": executor_result.review_results,
                        "final_decision": executor_result.final_decision,
                        "compliance_assessment": evaluator_result.compliance_assessment
                    }
                else:
                    logging.info(f"Henry has {len(evaluator_result.unfinished_tasks)} unfinished tasks, retrying...")
                    unfinished_tasks = evaluator_result.unfinished_tasks

            # 如果重试次数用完仍未完成
            logging.warning("Henry content review failed after maximum retries")
            return {
                "status": "failed",
                "plan": plan_result,
                "unfinished_tasks": unfinished_tasks,
                "retry_count": self.retries
            }

        except Exception as e:
            logging.error(f"Henry content review error: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def create_agents(self):
        """Create agent nodes"""
        self.planner_agent = create_planner_node(HenryPlannerResult, HENRY_PLANNER_SYSTEM_PROMPT)
        self.executor_agent = create_executor_node(HenryExecutorResult, HENRY_EXECUTOR_SYSTEM_PROMPT)
        self.evaluator_agent = create_evaluator_node(HenryEvaluatorResult, HENRY_EVALUATOR_SYSTEM_PROMPT)

    def check_platform_compliance(self, content: str, platform: Platform) -> PlatformComplianceResult:
        """检查平台合规性"""
        policy_config = self.platform_policies.get(platform, {})
        violations = []
        
        # 检查禁止内容
        prohibited_content = policy_config.get("prohibited_content", [])
        for prohibited in prohibited_content:
            if self._contains_prohibited_content(content, prohibited):
                violations.append(PolicyViolation(
                    policy_name=f"{platform.value}_content_policy",
                    violation_type="prohibited_content",
                    description=f"Content contains prohibited material: {prohibited}",
                    severity="high",
                    recommendation=f"Remove or modify content related to {prohibited}"
                ))
        
        # 检查广告要求
        if self._appears_commercial(content):
            advertising_requirements = policy_config.get("advertising_requirements", [])
            for requirement in advertising_requirements:
                if not self._meets_advertising_requirement(content, requirement):
                    violations.append(PolicyViolation(
                        policy_name=f"{platform.value}_advertising_policy",
                        violation_type="advertising_compliance",
                        description=f"Does not meet advertising requirement: {requirement}",
                        severity="medium",
                        recommendation=f"Ensure compliance with: {requirement}"
                    ))
        
        # 计算合规评分
        compliance_score = max(0.0, 1.0 - (len(violations) * 0.2))
        
        # 确定状态
        if len(violations) == 0:
            status = ComplianceStatus.APPROVED
        elif any(v.severity == "high" for v in violations):
            status = ComplianceStatus.REJECTED
        else:
            status = ComplianceStatus.NEEDS_MODIFICATION
        
        return PlatformComplianceResult(
            platform=platform,
            status=status,
            violations=violations,
            policy_version="latest",
            last_updated=datetime.now().isoformat(),
            compliance_score=compliance_score
        )

    def check_regional_compliance(self, content: str, region: Region) -> RegionalComplianceResult:
        """检查地区法规合规性"""
        law_config = self.regional_laws.get(region, {})
        
        # 检查禁止内容
        prohibited_content = law_config.get("prohibited_content", [])
        violations = []
        
        for prohibited in prohibited_content:
            if self._contains_prohibited_content(content, prohibited):
                violations.append(prohibited)
        
        # 检查基本要求
        basic_requirements = law_config.get("basic_requirements", [])
        missing_requirements = []
        
        for requirement in basic_requirements:
            if not self._meets_basic_requirement(content, requirement):
                missing_requirements.append(requirement)
        
        # 计算合规评分
        total_checks = len(prohibited_content) + len(basic_requirements)
        violations_count = len(violations) + len(missing_requirements)
        compliance_score = max(0.0, 1.0 - (violations_count / max(1, total_checks)))
        
        # 确定状态
        if violations_count == 0:
            status = ComplianceStatus.APPROVED
        elif len(violations) > 0:  # 有禁止内容
            status = ComplianceStatus.REJECTED
        else:  # 只是缺少要求
            status = ComplianceStatus.NEEDS_MODIFICATION
        
        return RegionalComplianceResult(
            region=region,
            status=status,
            legal_requirements=basic_requirements,
            prohibited_content=violations,
            mandatory_disclosures=missing_requirements,
            risk_assessment=self._assess_regional_risk(region, violations_count),
            compliance_score=compliance_score
        )

    def analyze_content(self, content: str) -> ContentAnalysis:
        """分析内容"""
        # 简化的内容分析实现
        sensitive_topics = self._detect_sensitive_topics(content)
        risk_factors = self._identify_risk_factors(content)
        
        return ContentAnalysis(
            language_detected=self._detect_language(content),
            sensitive_topics=sensitive_topics,
            sentiment_analysis=self._analyze_sentiment(content),
            content_category=self._categorize_content(content),
            risk_factors=risk_factors,
            content_quality=self._assess_content_quality(content)
        )

    def calculate_overall_risk(self, platform_results: List[PlatformComplianceResult], 
                             regional_results: List[RegionalComplianceResult]) -> float:
        """计算整体风险评分"""
        platform_risk = 1.0 - (sum(r.compliance_score for r in platform_results) / max(1, len(platform_results)))
        regional_risk = 1.0 - (sum(r.compliance_score for r in regional_results) / max(1, len(regional_results)))
        
        overall_risk = (
            platform_risk * self.risk_weights["platform_policy"] +
            regional_risk * self.risk_weights["regional_law"]
        )
        
        return min(1.0, overall_risk)

    # 辅助方法
    def _contains_prohibited_content(self, content: str, prohibited_type: str) -> bool:
        """检查是否包含禁止内容（简化实现）"""
        # 实际实现需要更复杂的NLP和关键词检测
        prohibited_keywords = {
            "仇恨言论": ["仇恨", "歧视", "种族主义"],
            "暴力威胁": ["威胁", "暴力", "伤害"],
            "误导信息": ["虚假", "谣言", "误导"],
            "成人内容": ["色情", "成人", "不雅"]
        }
        
        keywords = prohibited_keywords.get(prohibited_type, [])
        return any(keyword in content for keyword in keywords)

    def _appears_commercial(self, content: str) -> bool:
        """判断是否为商业内容"""
        commercial_indicators = ["购买", "优惠", "促销", "广告", "赞助", "合作"]
        return any(indicator in content for indicator in commercial_indicators)

    def _meets_advertising_requirement(self, content: str, requirement: str) -> bool:
        """检查是否满足广告要求"""
        if "标识" in requirement:
            return "#ad" in content or "#sponsored" in content or "广告" in content
        return True  # 简化实现

    def _meets_basic_requirement(self, content: str, requirement: str) -> bool:
        """检查是否满足基本要求"""
        if "标记" in requirement:
            return "AI生成" in content or "人工智能" in content
        return True  # 简化实现

    def _assess_regional_risk(self, region: Region, violations_count: int) -> str:
        """评估地区风险"""
        if violations_count == 0:
            return "低风险"
        elif violations_count <= 2:
            return "中风险"
        else:
            return "高风险"

    def _detect_sensitive_topics(self, content: str) -> List[str]:
        """检测敏感话题"""
        sensitive_keywords = {
            "政治": ["政治", "政府", "选举"],
            "宗教": ["宗教", "信仰", "神"],
            "健康": ["医疗", "健康", "疾病"]
        }
        
        detected = []
        for topic, keywords in sensitive_keywords.items():
            if any(keyword in content for keyword in keywords):
                detected.append(topic)
        
        return detected

    def _identify_risk_factors(self, content: str) -> List[str]:
        """识别风险因素"""
        risk_factors = []
        
        if len(content) > 2000:
            risk_factors.append("内容过长")
        
        if any(char in content for char in "!@#$%^&*"):
            risk_factors.append("特殊字符")
        
        return risk_factors

    def _detect_language(self, content: str) -> str:
        """检测语言（简化实现）"""
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > len(content) * 0.3:
            return "中文"
        return "英文"

    def _analyze_sentiment(self, content: str) -> str:
        """分析情感（简化实现）"""
        positive_words = ["好", "棒", "优秀", "amazing", "great", "excellent"]
        negative_words = ["坏", "差", "糟糕", "terrible", "bad", "awful"]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            return "积极"
        elif negative_count > positive_count:
            return "消极"
        else:
            return "中性"

    def _categorize_content(self, content: str) -> str:
        """内容分类（简化实现）"""
        if any(word in content for word in ["教程", "如何", "步骤"]):
            return "教程指南"
        elif any(word in content for word in ["新闻", "事件", "报道"]):
            return "新闻资讯"
        elif any(word in content for word in ["产品", "服务", "购买"]):
            return "商业推广"
        else:
            return "一般内容"

    def _assess_content_quality(self, content: str) -> float:
        """评估内容质量"""
        quality_score = 0.5  # 基础分
        
        # 长度适中加分
        if 100 <= len(content) <= 1000:
            quality_score += 0.2
        
        # 结构化内容加分
        if any(char in content for char in "。！？"):
            quality_score += 0.1
        
        # 有价值信息加分
        if any(word in content for word in ["如何", "为什么", "技巧", "方法"]):
            quality_score += 0.2
        
        return min(1.0, quality_score) 