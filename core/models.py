from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

    ideas = relationship("Idea", back_populates="user")


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    raw_input = Column(Text)
    evaluation_json = Column(Text)
    embedding_vector = Column(Text)
    category = Column(String)

    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    synthesis_output = Column(Text)

    user = relationship("User", back_populates="ideas")
    cluster = relationship("Cluster", back_populates="ideas")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    super_idea = Column(Text)
    merge_reasoning = Column(Text)

    ideas = relationship("Idea", back_populates="cluster")