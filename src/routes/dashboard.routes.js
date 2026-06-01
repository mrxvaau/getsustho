import { Router } from 'express';
import { requireAuth } from '../middleware/auth.js';
import { getDashboard } from '../services/hospital.service.js';

const router = Router();

router.get('/go', requireAuth, (req, res) => {
  if (req.currentProfile?.is_super_admin) return res.redirect('/superadmin');
  if (req.currentProfile?.role === 'PATIENT') return res.redirect('/patient');
  if (req.currentProfile?.role === 'DOCTOR') return res.redirect('/doctor');
  if (req.currentProfile?.role === 'HOSPITAL') return res.redirect('/hospital');
  if (req.currentProfile?.role === 'STAFF') return res.redirect('/staff');
  return res.redirect('/');
});

router.get('/superadmin', requireAuth, async (req, res, next) => {
  try {
    if (!req.currentProfile?.is_super_admin) return res.redirect('/go');
    const dashboard = await getDashboard(req.currentProfile);
    res.render('pages/dashboard', { title: 'Super Admin', mode: 'superadmin', dashboard });
  } catch (error) {
    return next(error);
  }
});

router.get('/patient', requireAuth, async (req, res, next) => {
  try {
    const dashboard = await getDashboard(req.currentProfile);
    res.render('pages/dashboard', { title: 'Patient Portal', mode: 'patient', dashboard });
  } catch (error) {
    return next(error);
  }
});

router.get('/doctor', requireAuth, async (req, res, next) => {
  try {
    const dashboard = await getDashboard(req.currentProfile);
    res.render('pages/dashboard', { title: 'Doctor Dashboard', mode: 'doctor', dashboard });
  } catch (error) {
    return next(error);
  }
});

router.get('/hospital', requireAuth, async (req, res, next) => {
  try {
    const dashboard = await getDashboard(req.currentProfile);
    res.render('pages/dashboard', { title: 'Hospital Dashboard', mode: 'hospital', dashboard });
  } catch (error) {
    return next(error);
  }
});

router.get('/staff', requireAuth, async (req, res, next) => {
  try {
    const dashboard = await getDashboard(req.currentProfile);
    res.render('pages/dashboard', { title: 'Staff Dashboard', mode: 'staff', dashboard });
  } catch (error) {
    return next(error);
  }
});

export default router;
