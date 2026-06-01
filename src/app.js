import express from 'express';
import session from 'express-session';
import flash from 'connect-flash';
import helmet from 'helmet';
import morgan from 'morgan';
import methodOverride from 'method-override';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import expressLayouts from 'express-ejs-layouts';
import { env } from './config/env.js';
import { attachAuthContext } from './middleware/auth.js';
import authRoutes from './routes/auth.routes.js';
import dashboardRoutes from './routes/dashboard.routes.js';
import publicRoutes from './routes/public.routes.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function createApp() {
  const app = express();

  app.set('view engine', 'ejs');
  app.set('views', path.join(__dirname, 'views'));
  app.set('layout', 'layouts/main');

  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(morgan(env.NODE_ENV === 'production' ? 'combined' : 'dev'));
  app.use(express.urlencoded({ extended: true }));
  app.use(express.json());
  app.use(methodOverride('_method'));
  app.use(express.static(path.join(__dirname, '..', 'public')));
  app.use(expressLayouts);
  app.use(session({
    name: 'getsustho.sid',
    secret: env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      sameSite: 'lax',
      secure: env.NODE_ENV === 'production',
      maxAge: 1000 * 60 * 60 * 24 * 7
    }
  }));
  app.use(flash());
  app.use(attachAuthContext);

  app.use('/', publicRoutes);
  app.use('/auth', authRoutes);
  app.use('/', dashboardRoutes);

  app.use((req, res) => {
    res.status(404).render('pages/error', {
      title: 'Page not found',
      status: 404,
      message: 'The page you are looking for does not exist.'
    });
  });

  app.use((err, req, res, next) => {
    console.error(err);
    res.status(err.status || 500).render('pages/error', {
      title: 'Something went wrong',
      status: err.status || 500,
      message: env.NODE_ENV === 'production' ? 'Please try again later.' : err.message
    });
  });

  return app;
}
