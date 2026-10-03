import { Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { Income } from '@/generated/prisma';

const prisma = new PrismaClient();

export const createIncome = async (req: Request, res: Response) => {
  try {
    const { userId, categoryId, amount, date, description } = req.body;
    const income: Income = await prisma.income.create({
      data: {
        userId,
        categoryId,
        amount,
        date,
        description
      }
    });
    res.status(201).json(income);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create income' });
  }
};

export const getIncomes = async (req: Request, res: Response) => {
  try {
    const { userId } = req.query;
    const incomes: Income[] = await prisma.income.findMany({
      where: { userId: Number(userId) }
    });
    res.status(200).json(incomes);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch incomes' });
  }
};

export const getIncome = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const income: Income | null = await prisma.income.findUnique({
      where: { id: Number(id) }
    });
    if (income) {
      res.status(200).json(income);
    } else {
      res.status(404).json({ error: 'Income not found' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch income' });
  }
};

export const updateIncome = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { userId, categoryId, amount, date, description } = req.body;
    const income: Income | null = await prisma.income.update({
      where: { id: Number(id) },
      data: {
        userId,
        categoryId,
        amount,
        date,
        description
      }
    });
    if (income) {
      res.status(200).json(income);
    } else {
      res.status(404).json({ error: 'Income not found' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to update income' });
  }
};

export const deleteIncome = async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const income: Income | null = await prisma.income.delete({
      where: { id: Number(id) }
    });
    if (income) {
      res.status(200).json(income);
    } else {
      res.status(404).json({ error: 'Income not found' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete income' });
  }
};