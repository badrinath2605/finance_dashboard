from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy import func, Date
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import models
import matplotlib
matplotlib.use('Agg')  
from io import BytesIO  
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import AsyncSessionLocal 
import base64
from datetime import datetime, date

app = FastAPI()


origins = ["http://localhost:3000",]  # Applications running on localhost:3000 are allowed

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str
    is_income: bool
    date: str

class GoalBase(BaseModel):
    date: date #= Field(..., description="Date in YYYY-MM-DD format")
    goal: str
    description: str

class TransactionModel(TransactionBase):
    id: int
    class Config:
        orm_mode = True

class GoalModel(GoalBase):
    id: int
    class Config:
        orm_mode = True

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


db_dependency = Annotated[AsyncSession, Depends(get_db)]


@app.post("/transactions", response_model=TransactionModel)
async def create_transaction(transaction: TransactionBase, db: db_dependency):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    await db.commit()  
    await db.refresh(db_transaction)  
    return db_transaction

@app.put("/transactions/{transaction_id}", response_model=TransactionModel)
async def update_transaction(transaction_id: int, updated_transaction: TransactionBase, db: db_dependency):
    transaction = await db.execute(select(models.Transaction).filter(models.Transaction.id == transaction_id))
    transaction = transaction.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for key, value in updated_transaction.dict().items():
        setattr(transaction, key, value)
    await db.commit()  
    await db.refresh(transaction)  
    return transaction

@app.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, db: db_dependency):
    transaction = await db.execute(select(models.Transaction).filter(models.Transaction.id == transaction_id))
    transaction = transaction.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await db.delete(transaction)
    await db.commit()  
    return {"detail": "Transaction deleted"}

@app.get("/transactions/total_sum")
async def get_total_sum(db: db_dependency):
    total_sum_query = select(func.sum(models.Transaction.amount)).where(models.Transaction.is_income == True)
    result = await db.execute(total_sum_query)
    total_checked = result.scalar()

    return {
        "total_income": total_checked if total_checked is not None else 0 
    }

# new changes from here
@app.get("/transactions/combined")
async def get_transactions_and_chart(db: db_dependency, skip: int = 0, limit: int = 5):
    result = await db.execute(select(models.Transaction).order_by(models.Transaction.date.asc()).offset(skip).limit(limit))
    transactions = result.scalars().all()
    def generate_chart(data, title, color):
        if not data.empty:  
            grouped_data = data.groupby('date').sum().reset_index()
            plt.figure(figsize=(10, 5))
            plt.bar(grouped_data['date'], grouped_data['amount'], color=color, alpha=0.7)
            plt.title(title, color='white')
            plt.xlabel('Date', color='white')
            plt.ylabel('Transaction Amount', color='white')
            plt.xticks(rotation=45, color='white')
            plt.yticks(color='white')
            plt.gca().set_facecolor('#1c1c1c')
            plt.gcf().set_facecolor('#1c1c1c')
            plt.grid(True, color='#444444')
            plt.tight_layout()
            buf = BytesIO()
            plt.savefig(buf, format='png', facecolor='#1c1c1c')
            buf.seek(0)
            plt.close()
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        else:
            return None 
    income_data = pd.DataFrame([{
        "amount": transaction.amount,
        "date": transaction.date,
        "is_income": transaction.is_income
    } for transaction in transactions if transaction.is_income == True])

    expense_data = pd.DataFrame([{
        "amount": transaction.amount,
        "date": transaction.date,
        "is_income": transaction.is_income
    } for transaction in transactions if transaction.is_income == False])
    income_chart = generate_chart(income_data, 'Income vs Date', '#00ccff')
    expense_chart = generate_chart(expense_data, 'Expense vs Date', '#ff0044')
    transaction_data = [{
        "id": transaction.id,
        "amount": transaction.amount,
        "date": transaction.date,
        "is_income": transaction.is_income,
        "category": transaction.category,
        "description": transaction.description
    } for transaction in transactions]
    return {
        "transactions": transaction_data,
        "chart_image": income_chart,
        "chart_image2": expense_chart
    }

@app.post("/goals")
async def set_budget(goal: GoalBase, db: db_dependency):
    db_goal = models.Goal(date=goal.date, goal=goal.goal, description=goal.description)  # Directly use goal.date
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal
    
@app.get("/budgets")
async def get_budget(db: db_dependency):
    result = await db.execute(select(models.Goal))
    goals = result.scalars().all()
    if not goals:
        raise HTTPException(status_code=404, detail="No goals found")
    return goals
