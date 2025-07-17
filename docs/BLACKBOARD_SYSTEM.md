# BlackBoard Multi-Tenant System Documentation

## Overview

The BlackBoard system is a comprehensive multi-tenant task management and collaboration platform designed for the Mercatus content factory. It provides shared visibility of all tasks across team members, with precise assignment down to expert instance level.

## Architecture

### Core Components

1. **BlackBoard Core** (`app/core/blackboard.py`)
   - Task lifecycle management
   - Expert instance coordination
   - Real-time state tracking
   - Performance analytics

2. **Team Manager** (`app/core/team_manager.py`)
   - Multi-tenant team management
   - Expert instance scaling
   - Auto-assignment algorithms
   - Team analytics

3. **Type System** (`app/types/blackboard.py`)
   - Comprehensive type definitions
   - Task state management
   - Expert role definitions
   - Team collaboration models

4. **API Controller** (`app/controllers/blackboard_controller.py`)
   - RESTful API endpoints
   - Request/response models
   - Authentication integration
   - Batch operations

## Key Features

### Multi-Tenant Architecture

- **Teams**: Isolated workspaces for different organizations
- **Expert Instances**: Multiple instances of each expert type per team
- **Shared Visibility**: All team members can see all tasks
- **Role-Based Access**: Different permission levels for team members

### Task Management

#### Task States
- `PENDING`: Newly created, awaiting assignment
- `ASSIGNED`: Assigned to an expert instance
- `IN_PROGRESS`: Currently being executed
- `COMPLETED`: Successfully finished
- `FAILED`: Execution failed
- `CANCELLED`: Manually cancelled

#### Task Priority Levels
- `URGENT`: Highest priority, immediate attention
- `HIGH`: Important tasks
- `MEDIUM`: Standard priority (default)
- `LOW`: Can be deferred

### Expert System

#### Expert Roles
- `PLANNER` (Jeff): Marketing strategy experts
- `EXECUTOR` (Monica): Content generation experts  
- `EVALUATOR` (Henry): Content review experts

#### Expert Instance Management
- Multiple instances per role per team
- Automatic load balancing
- Performance tracking
- Auto-scaling based on workload

## Data Models

### BlackboardTask

```python
class BlackboardTask(BaseModel):
    task_id: str
    team_id: str
    title: str
    description: str
    goal: str
    status: TaskStatus
    priority: TaskPriority
    required_expert_role: ExpertRole
    assignment: Optional[TaskAssignment]
    target_platforms: List[Platform]
    target_regions: List[Region]
    content_types: List[ContentType]
    dependencies: List[TaskDependency]
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_log: List[str]
    error_messages: List[str]
    metadata: TaskMetadata
```

### ExpertInstance

```python
class ExpertInstance(BaseModel):
    instance_id: str
    expert_role: ExpertRole
    instance_name: str
    status: str  # active, busy, offline
    max_concurrent_tasks: int
    current_task_count: int
    specializations: List[str]
    performance_metrics: Dict[str, float]
    created_at: datetime
    last_activity: datetime
```

### Team

```python
class Team(BaseModel):
    team_id: str
    team_name: str
    organization_id: str
    members: List[TeamMember]
    owner_id: str
    expert_instances: List[ExpertInstance]
    configuration: TeamConfiguration
    created_at: datetime
    updated_at: datetime
    is_active: bool
    total_tasks_completed: int
    total_content_generated: int
    team_performance_score: float
```

## API Reference

### Team Management

#### Create Team
```http
POST /blackboard/teams
{
    "team_name": "Marketing Team",
    "organization_id": "org_123",
    "owner_username": "john_doe"
}
```

#### Get Team Dashboard
```http
GET /blackboard/teams/{team_id}/dashboard
```

### Task Management

#### Create Marketing Workflow
```http
POST /blackboard/teams/{team_id}/workflows/marketing
{
    "project_name": "Q4 Campaign",
    "project_description": "End of year marketing campaign",
    "target_platforms": ["twitter", "facebook"],
    "target_regions": ["us", "eu"],
    "content_types": ["text", "text_image"],
    "priority": "high"
}
```

#### Create Custom Task
```http
POST /blackboard/teams/{team_id}/tasks
{
    "title": "Social Media Analysis",
    "description": "Analyze competitor social media presence",
    "goal": "Identify opportunities for improvement",
    "required_expert_role": "planner",
    "priority": "medium"
}
```

#### Search Tasks
```http
GET /blackboard/teams/{team_id}/tasks?status=pending&expert_role=executor&limit=20
```

#### Execute Task
```http
POST /blackboard/teams/{team_id}/tasks/{task_id}/execute
```

### Expert Management

#### Scale Experts
```http
POST /blackboard/teams/{team_id}/experts/scale
{
    "expert_role": "executor",
    "target_count": 5
}
```

#### Auto-Scale Team
```http
POST /blackboard/teams/{team_id}/experts/auto-scale
```

### Collaboration

#### Add Task Comment
```http
POST /blackboard/teams/{team_id}/tasks/{task_id}/comments
{
    "content": "This task needs more detail about target audience",
    "comment_type": "question"
}
```

## Usage Examples

### Creating a Complete Marketing Campaign

```python
from app.core.team_manager import team_manager
from app.types.blackboard import TaskPriority, ExpertRole
from app.types.output import Platform, Region, ContentType

# Create team
team = await team_manager.create_team(
    team_name="Marketing Team",
    organization_id="acme_corp",
    owner_id="user_123",
    owner_username="marketing_lead"
)

# Get BlackBoard
blackboard = team_manager.get_blackboard(team.team_id)

# Create planning task
planning_task = await blackboard.create_task(
    title="Q4 Campaign Strategy",
    description="Develop comprehensive Q4 marketing strategy",
    goal="Create platform-specific marketing plan with content calendar",
    required_expert_role=ExpertRole.PLANNER,
    creator_id="user_123",
    priority=TaskPriority.HIGH,
    target_platforms=[Platform.TWITTER, Platform.FACEBOOK],
    target_regions=[Region.USA, Region.EU],
    content_types=[ContentType.TEXT, ContentType.TEXT_IMAGE]
)

# Auto-assign task
await blackboard.auto_assign_task(planning_task.task_id)

# Execute task
result = await team_manager.execute_task(team.team_id, planning_task.task_id)
```

### Monitoring Team Performance

```python
# Get team dashboard
dashboard = await team_manager.get_team_dashboard(team.team_id)

# Check expert utilization
for expert in dashboard["expert_status"]:
    utilization = expert["utilization"]
    if utilization > 0.8:
        print(f"Expert {expert['name']} is highly utilized: {utilization:.1%}")

# Get performance metrics
performance = await blackboard.get_team_performance_metrics()
print(f"Team completion rate: {performance['completion_rate']:.1%}")
print(f"Average task duration: {performance['average_duration']:.1f} minutes")
```

### Auto-scaling Based on Workload

```python
# Check current workload
pending_tasks = await blackboard.get_tasks_by_status(TaskStatus.PENDING)
executor_tasks = [t for t in pending_tasks if t.required_expert_role == ExpertRole.EXECUTOR]

if len(executor_tasks) > 10:
    # Scale up Monica instances
    await team_manager.scale_experts(
        team.team_id, 
        ExpertRole.EXECUTOR, 
        target_count=5
    )
    
# Or use automatic scaling
scaling_result = await team_manager.auto_scale_team(team.team_id)
```

## Configuration

### Team Configuration

```python
from app.types.blackboard import TeamConfiguration

config = TeamConfiguration(
    max_jeff_instances=1,      # Maximum Jeff (planner) instances - Jeff is unique team leader
    max_monica_instances=5,    # Maximum Monica (executor) instances
    max_henry_instances=2,     # Maximum Henry (evaluator) instances
    auto_scaling_enabled=True, # Enable automatic scaling
    jeff_scaling_enabled=False,# Jeff never scales - unique leader
    task_queue_limit=100,      # Maximum tasks in queue
    concurrent_task_limit=20   # Maximum concurrent tasks
)
```

### Expert Specializations

```python
# Create expert with specializations
expert = await team_manager.create_expert_instance(
    team_id=team.team_id,
    expert_role=ExpertRole.EXECUTOR,
    instance_name="Monica - Social Media Specialist",
    max_concurrent_tasks=5,
    specializations=[
        "social_media",
        "short_form_content", 
        "twitter_optimization",
        "hashtag_strategy"
    ]
)
```

## Redis Storage Structure

### Key Patterns

- `blackboard:{team_id}:task:{task_id}` - Individual tasks
- `blackboard:{team_id}:state` - BlackBoard state
- `blackboard:{team_id}:expert:{instance_id}` - Expert instances
- `blackboard:{team_id}:event:{task_id}:{event_id}` - Task events
- `blackboard:{team_id}:comment:{task_id}:{comment_id}` - Task comments
- `team:{team_id}` - Team information

### Data Persistence

All task states, expert instances, and team configurations are persisted in Redis for:
- Fast access and updates
- Real-time collaboration
- System recovery
- Performance analytics

## Performance Optimization

### Task Assignment Algorithm

1. **Load Balancing**: Assign to expert with lowest current task count
2. **Specialization Matching**: Prefer experts with relevant specializations
3. **Performance History**: Consider past success rates
4. **Availability**: Only assign to active experts with capacity

### Auto-scaling Strategy

1. **Workload Analysis**: Monitor pending task queue length
2. **Utilization Metrics**: Track expert instance utilization rates
3. **Predictive Scaling**: Scale proactively based on patterns
4. **Cost Optimization**: Scale down unused instances

### Caching Strategy

- Task state caching for fast dashboard updates
- Performance metrics caching for analytics
- Expert availability caching for assignment
- Team configuration caching for validation

## Security Considerations

### Multi-tenancy Isolation

- Team-level data isolation in Redis
- User permission validation
- Organization-level access controls
- API rate limiting per team

### Data Protection

- Task data encryption at rest
- Secure expert instance communications
- Audit logging for all operations
- Compliance with data protection regulations

## Monitoring and Alerting

### Key Metrics

- Task completion rates per team
- Expert utilization rates
- Average task duration
- Failed task percentages
- System response times

### Alerts

- High task failure rates
- Expert instances offline
- Queue length exceeding limits
- Performance degradation
- Security violations

## Troubleshooting

### Common Issues

#### Tasks Stuck in Pending State
- Check expert availability
- Verify team configuration
- Review auto-assignment logs
- Manual assignment may be needed

#### Expert Instances Not Scaling
- Verify auto-scaling is enabled
- Check team configuration limits
- Review workload thresholds
- Manual scaling may be required

#### Performance Degradation
- Monitor Redis memory usage
- Check task queue lengths
- Review expert instance health
- Consider horizontal scaling

### Debug Commands

```python
# Get detailed task information
task = await blackboard.get_task(task_id)
print(f"Task status: {task.status}")
print(f"Assignment: {task.assignment}")
print(f"Execution log: {task.execution_log}")

# Check expert status
experts = await blackboard._get_all_expert_instances()
for expert in experts:
    print(f"{expert.instance_name}: {expert.status} ({expert.current_task_count}/{expert.max_concurrent_tasks})")

# Review team performance
metrics = await blackboard.get_team_performance_metrics()
print(f"Completion rate: {metrics['completion_rate']}")
print(f"Expert utilization: {metrics['expert_utilization']}")
```

## Migration and Deployment

### Database Migration

When upgrading from the existing system:

1. Export existing task data
2. Transform to new BlackBoard format
3. Create team structures
4. Import expert configurations
5. Validate data integrity

### Deployment Strategy

1. **Blue-Green Deployment**: Zero-downtime deployment
2. **Feature Flags**: Gradual rollout of new features
3. **Monitoring**: Comprehensive health checks
4. **Rollback Plan**: Quick reversion capability

## Future Enhancements

### Planned Features

- Real-time WebSocket notifications
- Advanced workflow automation
- Machine learning for task assignment
- Integration with external tools
- Enhanced analytics and reporting
- Mobile application support

### Scalability Improvements

- Horizontal scaling of BlackBoard instances
- Distributed task execution
- Multi-region deployment
- Performance optimization
- Advanced caching strategies

## Support and Maintenance

### Regular Maintenance

- Redis memory optimization
- Performance metrics review
- Security updates
- Data backup verification
- System health monitoring

### Support Procedures

- Issue tracking and resolution
- Performance optimization
- Feature requests
- Bug fixes
- Documentation updates

---

For additional support or questions about the BlackBoard system, please refer to the development team or create an issue in the project repository. 