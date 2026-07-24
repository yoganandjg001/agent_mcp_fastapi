import os
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()


def run_application():
    mcp_port = os.getenv("MCP_PORT", "8001")
    fastapi_port = os.getenv("FASTAPI_PORT", "8000")
    streamlit_port = os.getenv("STREAMLIT_PORT", "8501")

    print("==================================================")
    print("🚀 Starting Integrated Agentic Ops System")
    print("==================================================")
    print(f"Architecture:")
    print(f"  MCP Server (Port {mcp_port}) <- MCP Client <- LangGraph <- FastAPI (Port {fastapi_port}) <- Streamlit (Port {streamlit_port})")
    print("==================================================")

    # 1. Start Standalone MCP Server
    mcp_cmd = [sys.executable, "backend/mcp_service/mcp_server.py"]
    print(f"1. Starting Standalone MCP Server on http://localhost:{mcp_port}/sse ...")
    mcp_proc = subprocess.Popen(mcp_cmd)

    time.sleep(2)

    # 2. Start FastAPI Service
    fastapi_cmd = [sys.executable, "-m", "uvicorn", "backend.api.fastapi_app:app", "--host", "0.0.0.0", "--port", fastapi_port]
    print(f"2. Starting FastAPI Service on http://localhost:{fastapi_port} ...")
    fastapi_proc = subprocess.Popen(fastapi_cmd)
    
    time.sleep(2)

    # 3. Start Streamlit Web UI
    streamlit_cmd = [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", streamlit_port]
    print(f"3. Starting Streamlit Dashboard on http://localhost:{streamlit_port} ...")
    streamlit_proc = subprocess.Popen(streamlit_cmd)


    try:
        mcp_proc.wait()
        fastapi_proc.wait()
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        mcp_proc.terminate()
        fastapi_proc.terminate()
        streamlit_proc.terminate()


if __name__ == "__main__":
    run_application()
