import { createSupabaseClient } from '../config/supabase.js';
import { getProfileByUserId } from '../services/auth.service.js';

export async function attachAuthContext(req, res, next) {
  res.locals.flash = {
    success: req.flash('success'),
    error: req.flash('error'),
    info: req.flash('info')
  };
  res.locals.currentUser = null;
  res.locals.currentProfile = null;
  res.locals.path = req.path;

  const session = req.session.supabase;
  if (!session?.access_token) return next();

  try {
    const client = createSupabaseClient(session.access_token);
    const { data, error } = await client.auth.getUser(session.access_token);
    if (error || !data?.user) {
      delete req.session.supabase;
      return next();
    }

    const profile = await getProfileByUserId(data.user.id);
    req.supabase = client;
    req.currentUser = data.user;
    req.currentProfile = profile;
    res.locals.currentUser = data.user;
    res.locals.currentProfile = profile;
    return next();
  } catch (error) {
    return next(error);
  }
}

export function requireAuth(req, res, next) {
  if (!req.currentUser) {
    req.flash('error', 'Please sign in first.');
    return res.redirect('/auth/login');
  }
  return next();
}

export function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.currentUser) {
      req.flash('error', 'Please sign in first.');
      return res.redirect('/auth/login');
    }
    if (!roles.includes(req.currentProfile?.role)) {
      req.flash('error', 'Access denied.');
      return res.redirect('/go');
    }
    return next();
  };
}

export function requireSuperAdmin(req, res, next) {
  if (!req.currentUser) {
    req.flash('error', 'Please sign in first.');
    return res.redirect('/auth/login');
  }
  if (!req.currentProfile?.is_super_admin) {
    req.flash('error', 'Super admin access required.');
    return res.redirect('/go');
  }
  return next();
}
