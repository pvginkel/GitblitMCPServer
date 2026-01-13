mkdir -p $(pwd)/tmp

NAME=gitblit-mcp-server
ARGS="
    -p 8000:8000
    -e GITBLIT_URL=http://10.1.2.3:8080
"
