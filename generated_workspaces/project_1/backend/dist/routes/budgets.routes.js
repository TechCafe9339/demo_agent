import { Router } from 'express';
import { createBudget } from '../controllers/budgets.controller.js';
const router = Router();
router.post('/budgets', createBudget);
export default router;
//# sourceMappingURL=budgets.routes.js.map