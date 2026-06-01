import { Router } from 'express';
import { finishOAuth, signInWithPassword, signOut, signUpWithPassword, startOAuth } from '../services/auth.service.js';

const router = Router();

router.get('/login', (req, res) => {
  if (req.currentUser) return res.redirect('/go');
  return res.render('pages/login', { title: 'Login' });
});

router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const { session } = await signInWithPassword({ email, password });
    req.session.supabase = session;
    req.flash('success', 'Welcome back.');
    return res.redirect('/go');
  } catch (error) {
    if (error.message.includes('Supabase is not configured')) {
      req.flash('error', 'Supabase credentials are required before login can work.');
      return res.redirect('/');
    }
    req.flash('error', error.message);
    return res.redirect('/auth/login');
  }
});

router.get('/register/patient', (req, res) => {
  res.render('pages/register-patient', { title: 'Patient Registration' });
});

router.post('/register/patient', async (req, res) => {
  try {
    await signUpWithPassword({
      email: req.body.email,
      password: req.body.password,
      fullName: `${req.body.first_name || ''} ${req.body.last_name || ''}`.trim(),
      phone: req.body.phone,
      role: 'PATIENT'
    });
    req.flash('success', 'Account created. Please check your email if confirmation is enabled.');
    return res.redirect('/auth/login');
  } catch (error) {
    if (error.message.includes('Supabase is not configured')) {
      req.flash('error', 'Supabase credentials are required before registration can work.');
      return res.redirect('/');
    }
    req.flash('error', error.message);
    return res.redirect('/auth/register/patient');
  }
});

router.post('/oauth/:provider', async (req, res, next) => {
  try {
    const provider = req.params.provider;
    if (!['google', 'facebook'].includes(provider)) {
      req.flash('error', 'Unsupported login provider.');
      return res.redirect('/auth/login');
    }
    const url = await startOAuth(provider);
    return res.redirect(url);
  } catch (error) {
    return next(error);
  }
});

router.get('/callback', async (req, res, next) => {
  try {
    if (req.query.error_description) {
      req.flash('error', req.query.error_description);
      return res.redirect('/auth/login');
    }
    const session = await finishOAuth(req.query.code);
    req.session.supabase = session;
    req.flash('success', 'Signed in successfully.');
    return res.redirect('/go');
  } catch (error) {
    return next(error);
  }
});

router.post('/logout', async (req, res, next) => {
  try {
    await signOut(req.session.supabase?.access_token);
    req.session.destroy(() => res.redirect('/'));
  } catch (error) {
    return next(error);
  }
});

export default router;
