---
alwaysApply: true
---
## Frontend Project Rules (Next.js + Tailwind CSS)

### 🔄 Project Awareness & Context

- **Always read PLANNING.md** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check TASK.md** before starting a new task. If the task isn't listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in PLANNING.md and UI_DESIGN.md.

### 🧱 Code Structure & Modularity

- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or components.
- **Organize code into clearly separated modules and components**, grouped by feature or responsibility.
- **Use clear, consistent imports** following JavaScript/TypeScript and Next.js conventions:
  - External libraries first
  - Absolute imports for project modules (use jsconfig/tsconfig paths)
  - Relative imports for sibling components
- **Follow recommended Next.js project structure**:
  ```
  project/
  ├── app/ (or pages/)
  ├── components/
  ├── features/
  ├── hooks/
  ├── styles/
  ├── utils/
  ├── public/
  ├── tests/
  ├── tailwind.config.js
  ├── next.config.js
  └── package.json
  ```

### ✅ Task Completion

- **Mark completed tasks in TASK.md** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to TASK.md under a "Discovered During Work" section.

### 📎 Style & Structure

**Frontend Code Standards:**
- Use TypeScript for all components and logic
- Use functional components and React hooks
- Use descriptive variable and function names (camelCase for variables/functions, PascalCase for components)
- Keep components under 100 lines when possible
- Use Tailwind CSS utility classes for styling; avoid inline styles
- Extract repeated UI into reusable components
- Use prop-types or TypeScript interfaces for component props
- Structure files: imports, types/interfaces, constants, components, hooks, exports

**Naming Conventions:**
- camelCase for variables, functions, and file names
- PascalCase for React components and directories
- UPPER_CASE for constants
- Use lowercase with dashes for static asset folders (e.g., `user-avatars`)

**Component and Hook Design:**
- Write pure, stateless components when possible
- Use custom hooks for shared logic
- Implement single responsibility principle
- Use early returns and guard clauses
- Avoid deeply nested component trees

**Error Handling and Validation:**
- Handle API errors and edge cases early
- Use error boundaries for UI error handling
- Validate user input on both client and server
- Show user-friendly error messages
- Use loading and empty states for async data

**Performance and Best Practices:**
- Use React.memo and useCallback/useMemo for performance optimization
- Lazy load components/pages with dynamic imports
- Use SWR/React Query for data fetching and caching
- Optimize images with Next.js Image component
- Use context providers for global state when needed
- Minimize bundle size and avoid unnecessary dependencies

**Key Libraries and Patterns:**
- Use Next.js for routing, SSR/SSG, and API routes
- Use Tailwind CSS for styling and responsive design
- Use React Query or SWR for data fetching
- Use Jest and React Testing Library for testing
- Use ESLint, Prettier, and Husky for code quality

### 📚 Documentation & Explainability

- **Update README.md** when new features are added, dependencies change, or setup steps are modified.
- **Use comprehensive JSDoc/TypeScript doc comments** for complex functions and components
- **Comment complex logic** with inline comments explaining the reasoning
- **Maintain type stubs or interfaces for external data when needed**

### 🧠 AI Behavior Rules

- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified npm packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from TASK.md.
- **Use proper Next.js project structure with dependency management.**

### 🔧 Development Workflow

- **Use Node.js version specified in the project** (see .nvmrc or package.json)
- **Pin dependency versions** in package.json
- **Write tests first** when implementing new features (TDD approach)
- **Use pre-commit hooks** for code quality checks
- **Implement CI/CD** with GitHub Actions or Vercel for automated testing and deployment

### 🏗️ Architecture Patterns

- **Use dependency injection via React context or hooks for service layer components**
- **Implement repository/data fetching pattern for API access**
- **Use factory pattern for object/component creation when appropriate**
- **Apply SOLID principles in component and hook design**
- **Implement proper separation of concerns** between presentation (UI), business logic (hooks/services), and data access (API layer)

### 📱 Responsive & Accessibility

- **Use Tailwind CSS responsive utilities for all layouts and components**
- **Test UI on multiple screen sizes and devices**
- **Ensure keyboard navigation and ARIA attributes for all interactive elements**
- **Maintain color contrast and support dark mode**

### 🌍 Internationalization

- **Use next-i18next or react-i18next for multi-language support**
- **Externalize all user-facing text for translation**

### 🧪 Testing

- **Write unit and integration tests for all components, hooks, and utilities**
- **Use Jest and React Testing Library**
- **Aim for >80% code coverage**

### 🔒 Security

- **Sanitize all user input and output**
- **Use secure cookies or localStorage for tokens**
- **Implement route guards for protected pages**
- **Follow OWASP best practices for frontend security** 