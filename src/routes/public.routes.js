import { Router } from 'express';
import { getBlogPost, getBlogPosts, getDoctorProfile, getHospitalProfile, getLandingData, saveContactMessage } from '../services/hospital.service.js';

const router = Router();

function renderSetupIfNeeded(error, res) {
  if (error.message.includes('Supabase is not configured')) {
    res.status(200).render('pages/setup', { title: 'Setup Required' });
    return true;
  }
  return false;
}

router.get('/', async (req, res, next) => {
  try {
    const data = await getLandingData();
    res.render('pages/landing', { title: 'Smart Hospital Management', ...data });
  } catch (error) {
    if (renderSetupIfNeeded(error, res)) return;
    return next(error);
  }
});

router.post('/contact', async (req, res, next) => {
  try {
    await saveContactMessage({
      name: req.body.name,
      email: req.body.email,
      phone: req.body.phone || '',
      message: req.body.message
    });
    req.flash('success', 'Message sent. We will get back to you soon.');
    res.redirect('/#contact');
  } catch (error) {
    if (renderSetupIfNeeded(error, res)) return;
    return next(error);
  }
});

router.get('/doctor/:doctorId', async (req, res, next) => {
  try {
    const doctor = await getDoctorProfile(req.params.doctorId);
    if (!doctor) return next();
    res.render('pages/doctor-profile', { title: doctor.full_name, doctor });
  } catch (error) {
    if (renderSetupIfNeeded(error, res)) return;
    return next(error);
  }
});

router.get('/hospital/:id', async (req, res, next) => {
  try {
    const hospital = await getHospitalProfile(req.params.id);
    if (!hospital) return next();
    res.render('pages/hospital-profile', { title: hospital.name, hospital });
  } catch (error) {
    if (renderSetupIfNeeded(error, res)) return;
    return next(error);
  }
});

router.get('/blog', async (req, res, next) => {
  try {
    const posts = await getBlogPosts();
    res.render('pages/blog-list', { title: 'Blog', posts });
  } catch (error) {
    if (renderSetupIfNeeded(error, res)) return;
    return next(error);
  }
});

router.get('/blog/:slug', async (req, res, next) => {
  try {
    const post = await getBlogPost(req.params.slug);
    if (!post) return next();
    res.render('pages/blog-detail', { title: post.title, post });
  } catch (error) {
    return next(error);
  }
});

export default router;
