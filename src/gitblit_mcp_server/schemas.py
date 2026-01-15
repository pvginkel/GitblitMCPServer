"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field  # type: ignore


# Repository schemas
class Repository(BaseModel):  # type: ignore[misc]
    """Repository information."""

    name: str = Field(..., description="Full repository name (e.g., 'team/project.git')")
    description: str = Field(..., description="Repository description")
    lastChange: str | None = Field(None, description="ISO 8601 timestamp of last change")
    hasCommits: bool = Field(..., description="Whether repository has any commits")


class ListReposResponse(BaseModel):  # type: ignore[misc]
    """Response from list repositories endpoint."""

    repositories: list[Repository]
    totalCount: int = Field(..., description="Total number of matching repositories")
    limitHit: bool = Field(..., description="Whether more results exist beyond current page")


# File listing schemas
class FileInfo(BaseModel):  # type: ignore[misc]
    """File or directory information."""

    path: str = Field(..., description="File or directory path (directories end with '/')")
    isDirectory: bool = Field(..., description="Whether this is a directory")


class ListFilesResponse(BaseModel):  # type: ignore[misc]
    """Response from list files endpoint."""

    files: list[FileInfo]
    totalCount: int = Field(..., description="Total number of files in directory")
    limitHit: bool = Field(..., description="Whether more files exist beyond current page")


# File content schemas
class ReadFileResponse(BaseModel):  # type: ignore[misc]
    """Response from read file endpoint."""

    content: str = Field(
        ..., description="File content with line numbers prefixed (e.g., '1: line one\\n2: line two')"
    )


# File search schemas
class SearchChunk(BaseModel):  # type: ignore[misc]
    """A chunk of matching code with context."""

    startLine: int = Field(..., description="1-based starting line number")
    endLine: int = Field(..., description="1-based ending line number (inclusive)")
    content: str = Field(..., description="Chunk content with line numbers prefixed")


class FileSearchResult(BaseModel):  # type: ignore[misc]
    """A file search result."""

    repository: str = Field(..., description="Repository name")
    path: str = Field(..., description="File path within repository")
    branch: str | None = Field(None, description="Branch name")
    commitId: str | None = Field(None, description="Commit SHA")
    chunks: list[SearchChunk] = Field(..., description="Matching code chunks with context")


class FileSearchResponse(BaseModel):  # type: ignore[misc]
    """Response from file search endpoint."""

    query: str = Field(..., description="The executed search query")
    totalCount: int = Field(..., description="Total number of matches found")
    limitHit: bool = Field(..., description="Whether results were truncated due to limit")
    results: list[FileSearchResult]


# Commit search schemas
class CommitSearchResult(BaseModel):  # type: ignore[misc]
    """A commit search result."""

    repository: str = Field(..., description="Repository name")
    commit: str = Field(..., description="Commit SHA")
    author: str = Field(..., description="Commit author")
    committer: str | None = Field(None, description="Committer name")
    date: str = Field(..., description="ISO 8601 timestamp")
    title: str = Field(..., description="First line of commit message")
    message: str = Field(..., description="Full commit message")
    branch: str | None = Field(None, description="Branch name")


class CommitSearchResponse(BaseModel):  # type: ignore[misc]
    """Response from commit search endpoint."""

    query: str = Field(..., description="The executed search query")
    totalCount: int = Field(..., description="Total number of matches found")
    limitHit: bool = Field(..., description="Whether results were truncated due to limit")
    commits: list[CommitSearchResult]


# Find files schemas
class FindFilesResult(BaseModel):  # type: ignore[misc]
    """A repository's matching files."""

    repository: str = Field(..., description="Repository name")
    revision: str | None = Field(None, description="Resolved revision reference")
    files: list[str] = Field(..., description="List of matching file paths")


class FindFilesResponse(BaseModel):  # type: ignore[misc]
    """Response from find files endpoint."""

    pattern: str = Field(..., description="The glob pattern that was searched")
    totalCount: int = Field(..., description="Total number of matching files found")
    limitHit: bool = Field(..., description="Whether results were truncated due to limit")
    results: list[FindFilesResult]


# Error schemas
class ErrorDetail(BaseModel):  # type: ignore[misc]
    """Error detail information."""

    code: str = Field(..., description="Error code (e.g., 'NOT_FOUND', 'INVALID_REQUEST')")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):  # type: ignore[misc]
    """Error response format."""

    error: ErrorDetail


class GitblitAPIError(Exception):
    """Exception raised when Gitblit API returns an error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
