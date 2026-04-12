-- PS-14: Link exports to jobs for payment tracking
ALTER TABLE public.exports ADD COLUMN IF NOT EXISTS job_id uuid REFERENCES public.jobs(id);
CREATE INDEX IF NOT EXISTS idx_exports_job_id ON public.exports(job_id);
