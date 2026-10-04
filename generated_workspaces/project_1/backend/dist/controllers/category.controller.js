import { prisma } from '../config/prisma.ts';
export class CategoryController {
    async createCategory(req, res) {
        try {
            const { name, type } = req.body;
            const category = await prisma.category.create({
                data: {
                    name,
                    type
                }
            });
            res.status(201).json(category);
        }
        catch (error) {
            console.error(error instanceof Error
                ? error.message
                : error);
            res.status(500).json({ error: 'Failed to create category' });
        }
    }
    async getCategories(req, res) {
        try {
            const categories = await prisma.category.findMany();
            res.json(categories);
        }
        catch (error) {
            console.error(error instanceof Error
                ? error.message
                : error);
            res.status(500).json({ error: 'Failed to fetch categories' });
        }
    }
    async getCategoryById(req, res) {
        try {
            const { id } = req.params;
            const category = await prisma.category.findUnique({
                where: { id: parseInt(id) }
            });
            if (category) {
                res.json(category);
            }
            else {
                res.status(404).json({ error: 'Category not found' });
            }
        }
        catch (error) {
            console.error(error instanceof Error
                ? error.message
                : error);
            res.status(500).json({ error: 'Failed to fetch category' });
        }
    }
    async updateCategory(req, res) {
        try {
            const { id } = req.params;
            const { name, type } = req.body;
            const category = await prisma.category.update({
                where: { id: parseInt(id) },
                data: { name, type }
            });
            res.json(category);
        }
        catch (error) {
            console.error(error instanceof Error
                ? error.message
                : error);
            res.status(500).json({ error: 'Failed to update category' });
        }
    }
    async deleteCategory(req, res) {
        try {
            const { id } = req.params;
            await prisma.category.delete({
                where: { id: parseInt(id) }
            });
            res.status(204).send();
        }
        catch (error) {
            console.error(error instanceof Error
                ? error.message
                : error);
            res.status(500).json({ error: 'Failed to delete category' });
        }
    }
}
//# sourceMappingURL=category.controller.js.map