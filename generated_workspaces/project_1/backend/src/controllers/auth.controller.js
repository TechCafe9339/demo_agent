import { AuthService } from '../services/auth.service';
export class AuthController {
    authService;
    constructor() {
        this.authService = new AuthService();
    }
    login = async (req, res) => {
        try {
            const { email, password } = req.body;
            const user = await this.authService.validateUser(email, password);
            const token = await this.authService.generateToken(user);
            res.status(200).json({ token });
        }
        catch (error) {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    };
    register = async (req, res) => {
        try {
            const { email, password } = req.body;
            const user = await this.authService.registerUser(email, password);
            const token = await this.authService.generateToken(user);
            res.status(201).json({ token });
        }
        catch (error) {
            res.status(500).json({ error: 'Registration failed' });
        }
    };
}
