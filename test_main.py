from langgraph_supervisor import create_supervisor

if __name__ == "__main__":
    # 创建监督者工作流

    workflow = create_supervisor(
        [content_grabber, content_generator, content_publisher],
        model="openai:gpt-4o",
        prompt="You are a supervisor managing content creation agents."
    )

    # 编译并运行
    app = workflow.compile()
    result = app.invoke({
        "messages": [{"role": "user", "content": "create a blog post about AI trends"}]
    })