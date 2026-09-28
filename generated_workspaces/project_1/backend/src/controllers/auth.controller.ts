import { Request, Response } from 'express';
import { prisma } from '../config/prisma';
import { AuthService } from '../services/auth.service';
import { AuthMiddleware } from '../middleware/auth.middleware';

export class AuthController {
  private authService: AuthService;

  constructor() {
    this.authService = new AuthService();
  }

  public login = async (req: Request, res: Response): Promise<void> => {
    try {
      const { email, password } = req.body;
      const user = await authService.validateUser(email, password);
      const token = await this.authService.generateToken(user);
      res.status(200).json({ token });
    } catch (error) {
      res.status(401).json({ error: 'Invalid credentials' });
    }
  }

  public register = async (req: Request, res: Response): Promise<void> => {
    try {
      const { email, password } = req.body;
      const user = await this.authService.registerUser(email, password);
      const token = await this.authService.generateToken(user);
      res.status(201).json({ token });
    } catch (error) {
      res.status(500).json({ error: 'Registration failed' });
    }
  }
}