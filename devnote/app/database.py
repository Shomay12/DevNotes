from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from devnote.app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enable SQLite foreign key constraints & WAL mode for concurrency and atomic reliability
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from devnote.app.models.notebook import Notebook
    from devnote.app.models.snippet import Snippet
    from devnote.app.models.execution import ExecutionRecord
    from devnote.app.models.search_history import SearchHistory
    from devnote.app.models.saved_resource import SavedResource
    from devnote.app.models.doc_index import DocIndex
    Base.metadata.create_all(bind=engine)

    # Initialize SQLite FTS5 table for offline documentation search
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS doc_entries_fts USING fts5(
                    index_id,
                    title,
                    category,
                    language,
                    url,
                    content,
                    code
                );
            """))
            conn.commit()
    except Exception as e:
        print(f"Notice: FTS5 table initialization: {e}")

# Ensure tables are created on module import
init_db()

def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
