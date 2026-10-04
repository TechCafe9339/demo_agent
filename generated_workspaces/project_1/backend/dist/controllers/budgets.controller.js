import { prisma } from '../config/prisma.js';
export async function createBudget(req, res) {
    const { userId, categoryId, budgetAmount, month } = req.body;
    try {
        const budget = await prisma.budget.create({
            data: {
                userId,
                categoryId,
                budgetAmount: parseFloat(budgetAmount),
                month: new Date(month)
            }
        });
        res.status(201).json(budget);
    }
    catch (error) {
        console.error(error instanceof Error
            ? error.message
            : error);
        res.status(500).json({ error: 'Failed to create budget' });
    }
}
//# sourceMappingURL=budgets.controller.js.map