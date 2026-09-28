import { verify } from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
const prisma = new PrismaClient();
export const authenticateToken = (req, res, next) => {
    const authHeader = req.headers.authorization;
    let token = '';
    if (authHeader) {
        const parts = authHeader.split(' ');
        if (parts.length === 2 && parts[0] === 'Bearer') {
            token = parts[1];
        }
    }
    if (!token) {
        return res.status(401).json({ error: 'Access denied' });
    }
    try {
        const decoded = verify(token, process.env.JWT_SECRET || 'your_jwt_secret_key');
        const user = await prisma.user.findUnique({ where: { id: decoded.userId } });
        if (!user) {
            throw new Error('User not found');
        }
        req.user = user;
        next();
    }
    catch (error) {
        return res.status(403).json({ error: 'Invalid token' });
    }
};
