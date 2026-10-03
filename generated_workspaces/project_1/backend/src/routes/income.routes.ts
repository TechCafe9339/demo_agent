import { Router } from 'express';
import { createIncome, getIncomes, getIncome, updateIncome, deleteIncome } from '@/controllers/income.controller';

const router = Router();

router.post('/incomes', createIncome);
router.get('/incomes', getIncomes);
router.get('/incomes/:id', getIncome);
router.put('/incomes/:id', updateIncome);
router.delete('/incomes/:id', deleteIncome);

export default router;