# Mermaid Cheat Sheet

## Flowchart

```mermaid
flowchart TD
  A[Start] --> B{Decision}
  B -->|Yes| C[Action]
  B -->|No| D[End]
```

## Sequence Diagram

```mermaid
sequenceDiagram
  participant U as User
  participant A as API
  U->>A: Request
  A-->>U: Response
```

## State Diagram

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Running: start
  Running --> Idle: stop
```

## Class Diagram

```mermaid
classDiagram
  class User {
    +String id
    +login()
  }
  class Session {
    +String token
  }
  User "1" --> "*" Session
```

## ER Diagram

```mermaid
erDiagram
  USER ||--o{ ORDER : places
  USER {
    int id PK
    string email
  }
  ORDER {
    int id PK
    int user_id FK
  }
```

## Useful Style and Layout

- Use `flowchart TD` for top-down and `flowchart LR` for left-right.
- Use `subgraph` to group related nodes.
- Keep labels short; move long explanation outside the diagram.
- Use stable IDs and readable labels:
  - Good: `AuthSvc[Auth Service]`
  - Avoid: `Node-1[Very long sentence ...]`
