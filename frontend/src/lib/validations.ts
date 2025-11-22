/**
 * Form Validation Schemas
 * Using Zod for runtime type checking and validation
 */

import { z } from 'zod';
import { IncidentType, SeverityLevel } from '@/types/incident';

/**
 * Incident Report Form Schema
 */
export const incidentReportSchema = z.object({
  incident_type: z.nativeEnum(IncidentType, {
    errorMap: () => ({ message: 'Please select an incident type' }),
  }),

  severity: z.nativeEnum(SeverityLevel, {
    errorMap: () => ({ message: 'Please select a severity level' }),
  }),

  description: z
    .string()
    .min(10, 'Description must be at least 10 characters')
    .max(1000, 'Description must not exceed 1000 characters')
    .refine((val) => val.trim().length >= 10, {
      message: 'Description cannot be just whitespace',
    }),

  location: z.object({
    type: z.literal('Point'),
    coordinates: z.tuple([
      z.number().min(-180).max(180), // longitude
      z.number().min(-90).max(90),   // latitude
    ]),
  }),

  timestamp: z.string().refine(
    (val) => {
      // Accept both full ISO datetime and datetime-local format (YYYY-MM-DDTHH:mm)
      const date = new Date(val);
      return !isNaN(date.getTime()) && date.getTime() > 0;
    },
    {
      message: 'Please provide a valid date and time',
    }
  ),

  // Optional fields
  casualties: z
    .object({
      killed: z.number().min(0).default(0),
      injured: z.number().min(0).default(0),
      missing: z.number().min(0).default(0),
    })
    .optional(),

  reporter_phone: z
    .string()
    .regex(/^\+?[1-9]\d{1,14}$/, 'Invalid phone number format')
    .optional()
    .or(z.literal('')),

  is_anonymous: z.boolean().default(false),

  media_urls: z.array(z.string().url('Invalid URL')).optional(),

  tags: z.array(z.string().min(2).max(50)).optional(),
});

export type IncidentReportFormData = z.infer<typeof incidentReportSchema>;

/**
 * Nearby Search Form Schema
 */
export const nearbySearchSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  radius_km: z.number().min(1).max(500).default(50),
  days: z.number().min(1).max(365).default(30),
  incident_types: z.string().optional(),
  severities: z.string().optional(),
  verified_only: z.boolean().default(false),
});

export type NearbySearchFormData = z.infer<typeof nearbySearchSchema>;
