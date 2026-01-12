# Gitblit MCP Server - Product Brief

## Overview

Gitblit MCP Server is a Model Context Protocol (MCP) server that enables AI assistants and LLM-based tools to interact with Gitblit-hosted Git repositories. It provides a standardized interface for repository browsing, file access, and full-text search capabilities.

## Target Audience

- **AI/LLM Tool Developers**: Building code assistants that need access to Gitblit repositories
- **Development Teams**: Using Gitblit for Git hosting who want to integrate AI-powered code analysis
- **Enterprise Users**: Organizations running self-hosted Gitblit instances seeking MCP integration

## Primary Features

- **Repository Discovery**: List and search available repositories
- **File Browsing**: Navigate directory structures and list files within repositories
- **File Content Access**: Read file contents with support for specific revisions/branches
- **Full-Text Search**: Search across file contents and commit history using Gitblit's Lucene index
  - File content search (blob search)
  - Commit message and metadata search

## Architecture

```
┌─────────────────┐     MCP Protocol      ┌─────────────────────┐
│   MCP Client    │◄────────────────────►│  Gitblit MCP Server │
│  (AI Assistant) │                       │    (Python/FastMCP) │
└─────────────────┘                       └──────────┬──────────┘
                                                     │ HTTP/JSON
                                                     ▼
                                          ┌─────────────────────┐
                                          │  Gitblit Search     │
                                          │   API Plugin        │
                                          │     (Java)          │
                                          └──────────┬──────────┘
                                                     │
                                                     ▼
                                          ┌─────────────────────┐
                                          │      Gitblit        │
                                          │  (Git Repositories) │
                                          └─────────────────────┘
```

### Components

1. **Gitblit MCP Server** (this project)
   - Python application using FastMCP framework
   - Implements MCP protocol for AI tool integration
   - Translates MCP requests to Search API Plugin calls

2. **Gitblit Search API Plugin** (companion project)
   - Java plugin for Gitblit
   - Exposes repository, file, and search operations via REST API
   - Leverages Gitblit's internal services and Lucene search index

## Technology Stack

- **MCP Server**: Python 3.10+, FastMCP
- **Search Plugin**: Java 8+, Gitblit Plugin Framework (pf4j)
- **Deployment**: Docker containers, Kubernetes-ready
