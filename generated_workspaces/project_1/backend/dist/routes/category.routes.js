import { Router } from 'express';
import { CategoryController } from '../controllers/category.controller';
export function categoryRoutes(app) {
    const router = Router();
    router.post('/categories', CategoryController.createCategory);
    router.get('/categories', CategoryController.getCategories);
    router.get('/categories/:id', CategoryController.getCategoryById);
    router.put('/categories/:id', CategoryController.updateCategory);
    router.delete('/categories/:id', CategoryController.deleteCategory);
    app.use('/api', router);
}
//# sourceMappingURL=category.routes.js.map