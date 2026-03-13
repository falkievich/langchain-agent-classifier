from fastapi import FastAPI
from routes.llm_agent_routes import router as llm_agent_routes

app = FastAPI(title="Agente Inteligente Clasificador de Expedientes Judiciales")

# Routers de los endpoints
app.include_router(llm_agent_routes, prefix="/api")
