from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
import random

# Configuração do Banco de Dados SQLite local
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

# Modelo da Perk (Habilidade do DbD)
class Perk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    role: str  # "survivor" ou "killer"
    description: str

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Função para popular dados iniciais se o banco estiver vazio
def seed_db():
    with Session(engine) as session:
        perks_count = session.exec(select(Perk)).first()
        if not perks_count:
            initial_perks = [
                # Sobrevivente
                Perk(name="Balanced Landing", role="survivor", description="Reduz o desvio de queda e dá bônus de velocidade ao cair."),
                Perk(name="Déjà Vu", role="survivor", description="Mostra a aura de 3 geradores próximos uns dos outros."),
                Perk(name="We'll Make It", role="survivor", description="Aumenta a velocidade de cura após desenganchar alguém."),
                Perk(name="Resilience", role="survivor", description="Aumenta a velocidade de reparo, cura e outras ações quando ferido."),
                Perk(name="Adrenaline", role="survivor", description="Cura um estado de saúde e dá bônus de corrida quando os geradores são ativados."),
                Perk(name="Sprint Burst", role="survivor", description="Começa a correr disparada ao iniciar a corrida, gerando fadiga depois."),
                
                # Assassino (Killer)
                Perk(name="I'm All Ears", role="killer", description="Mostra a aura do Sobrevivente ao fazer um salto rápido em rush."),
                Perk(name="Thrilling Tremors", role="killer", description="Bloqueia geradores temporariamente após carregar um sobrevivente."),
                Perk(name="Spies from the Shadows", role="killer", description="Corvos avisam quando um sobrevivente passa correndo por perto."),
                Perk(name="Discordance", role="killer", description="Avisa quando 2 ou mais sobreviventes consertam o mesmo gerador."),
                Perk(name="Pop Goes the Weasel", role="killer", description="Após pendurar alguém, chutar um gerador regride instantaneamente a progressão."),
                Perk(name="NOED (No One Escapes Death)", role="killer", description="Concede exposição (instakill) e velocidade extra quando os geradores são concluídos.")
            ]
            for perk in initial_perks:
                session.add(perk)
            session.commit()

app = FastAPI(title="DbD Build Randomizer API", version="1.0")

# Permitir CORS para o frontend conversar com o backend sem conflito
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_db()

@app.get("/")
def root():
    return {"message": "Bem-vindo à API do Randomizador de Builds do DbD!"}

@app.get("/randomize/{role}")
def randomize_build(role: str):
    role = role.lower()
    if role not in ["survivor", "killer"]:
        raise HTTPException(status_code=400, detail="Role inválido. Use 'survivor' ou 'killer'.")
    
    with Session(engine) as session:
        statement = select(Perk).where(Perk.role == role)
        perks = session.exec(statement).all()
        
        if len(perks) < 4:
            raise HTTPException(status_code=500, detail="Não há perks suficientes cadastradas para sortear.")
        
        # Sorteia 4 perks aleatórias sem repetição
        selected_perks = random.sample(perks, 4)
        return {"role": role, "build": selected_perks}