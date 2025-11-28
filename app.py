from fastapi import FastAPI
from routes.llm_agent_routes import router as llm_agent_routes
from routes.person_extraction_routes import router as person_extraction_routes

app = FastAPI(title="Agente Inteligente Clasificador con LangChain")

# Routers de los endpoints
app.include_router(llm_agent_routes, prefix="/api")
app.include_router(person_extraction_routes, prefix="/api")
