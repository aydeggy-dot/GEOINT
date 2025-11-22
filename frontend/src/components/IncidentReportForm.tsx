/**
 * IncidentReportForm Component
 * Form for reporting new security incidents
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { incidentService } from '@/services/api';
import { incidentReportSchema, type IncidentReportFormData } from '@/lib/validations';
import {
  IncidentType,
  SeverityLevel,
  incidentTypeLabels,
  severityLabels,
} from '@/types/incident';
import { getCurrentLocation, isInNigeria } from '@/utils/mapConfig';
import { toast } from 'sonner';

interface IncidentReportFormProps {
  onSuccess?: () => void;
  initialLocation?: [number, number]; // [lng, lat]
}

export default function IncidentReportForm({
  onSuccess,
  initialLocation,
}: IncidentReportFormProps) {
  const [showCasualties, setShowCasualties] = useState(false);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const queryClient = useQueryClient();

  // Get current datetime in local timezone for datetime-local input
  const getCurrentLocalDateTime = () => {
    const now = new Date();
    // Adjust for timezone offset
    const offset = now.getTimezoneOffset() * 60000;
    const localTime = new Date(now.getTime() - offset);
    return localTime.toISOString().slice(0, 16);
  };

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<IncidentReportFormData>({
    resolver: zodResolver(incidentReportSchema),
    defaultValues: {
      timestamp: getCurrentLocalDateTime(),
      location: initialLocation
        ? {
            type: 'Point',
            coordinates: initialLocation,
          }
        : undefined,
      is_anonymous: false,
      casualties: {
        killed: 0,
        injured: 0,
        missing: 0,
      },
    },
  });

  const location = watch('location');
  const isAnonymous = watch('is_anonymous');

  // Create incident mutation
  const createMutation = useMutation({
    mutationFn: incidentService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incidents-geojson'] });
      queryClient.invalidateQueries({ queryKey: ['incidents'] });
      toast.success('Incident reported successfully!');
      if (onSuccess) onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit report');
    },
  });

  // Get current location
  const handleGetLocation = async () => {
    setIsGettingLocation(true);
    try {
      const position = await getCurrentLocation();
      const { longitude, latitude } = position.coords;

      if (!isInNigeria(longitude, latitude)) {
        toast.error('Location must be within Nigeria');
        return;
      }

      setValue('location', {
        type: 'Point',
        coordinates: [longitude, latitude],
      });

      toast.success('Location obtained successfully');
    } catch (error) {
      toast.error('Failed to get location. Please enable location services.');
    } finally {
      setIsGettingLocation(false);
    }
  };

  // Handle form submission
  const onSubmit = async (data: IncidentReportFormData) => {
    // Convert timestamp to ISO format if needed
    const timestampISO = data.timestamp.includes('T')
      ? new Date(data.timestamp).toISOString()
      : data.timestamp;

    // Clean up empty optional fields
    const payload = {
      ...data,
      timestamp: timestampISO,
      reporter_phone: data.reporter_phone || undefined,
      casualties: showCasualties ? data.casualties : undefined,
      media_urls: data.media_urls?.filter((url) => url.trim()) || undefined,
      tags: data.tags?.filter((tag) => tag.trim()) || undefined,
    };

    await createMutation.mutateAsync(payload);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Incident Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Incident Type <span className="text-red-500">*</span>
        </label>
        <select
          {...register('incident_type')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
        >
          <option value="">Select incident type</option>
          {Object.entries(incidentTypeLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {errors.incident_type && (
          <p className="mt-1 text-sm text-red-600">{errors.incident_type.message}</p>
        )}
      </div>

      {/* Severity Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Severity Level <span className="text-red-500">*</span>
        </label>
        <select
          {...register('severity')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
        >
          <option value="">Select severity</option>
          {Object.entries(severityLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {errors.severity && (
          <p className="mt-1 text-sm text-red-600">{errors.severity.message}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          {...register('description')}
          rows={4}
          placeholder="Describe what happened... (minimum 10 characters)"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      {/* Location */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Location <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleGetLocation}
            disabled={isGettingLocation}
            className="flex items-center gap-2 px-4 py-2 bg-nigeria-green hover:bg-green-700 text-white rounded-md transition-colors disabled:bg-gray-400"
          >
            {isGettingLocation ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Getting location...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                Use My Location
              </>
            )}
          </button>

          {location && (
            <div className="flex-1 px-3 py-2 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
              Location set: {location.coordinates[1].toFixed(6)}°N,{' '}
              {location.coordinates[0].toFixed(6)}°E
            </div>
          )}
        </div>
        {errors.location && (
          <p className="mt-1 text-sm text-red-600">Location is required</p>
        )}
      </div>

      {/* Timestamp */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          When did this occur? <span className="text-red-500">*</span>
        </label>
        <input
          type="datetime-local"
          {...register('timestamp')}
          max={getCurrentLocalDateTime()}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
        />
        {errors.timestamp && (
          <p className="mt-1 text-sm text-red-600">{errors.timestamp.message}</p>
        )}
      </div>

      {/* Casualties (optional) */}
      <div>
        <label className="flex items-center gap-2 cursor-pointer mb-2">
          <input
            type="checkbox"
            checked={showCasualties}
            onChange={(e) => setShowCasualties(e.target.checked)}
            className="w-4 h-4 text-nigeria-green border-gray-300 rounded focus:ring-nigeria-green"
          />
          <span className="text-sm font-medium text-gray-700">
            Report casualties (if any)
          </span>
        </label>

        {showCasualties && (
          <div className="grid grid-cols-3 gap-4 mt-2">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Killed</label>
              <input
                type="number"
                {...register('casualties.killed', { valueAsNumber: true })}
                min="0"
                defaultValue={0}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Injured</label>
              <input
                type="number"
                {...register('casualties.injured', { valueAsNumber: true })}
                min="0"
                defaultValue={0}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Missing</label>
              <input
                type="number"
                {...register('casualties.missing', { valueAsNumber: true })}
                min="0"
                defaultValue={0}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent"
              />
            </div>
          </div>
        )}
      </div>

      {/* Reporter Phone (optional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Contact Phone Number (optional)
        </label>
        <input
          type="tel"
          {...register('reporter_phone')}
          placeholder="+234..."
          disabled={isAnonymous}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-nigeria-green focus:border-transparent disabled:bg-gray-100"
        />
        {errors.reporter_phone && (
          <p className="mt-1 text-sm text-red-600">{errors.reporter_phone.message}</p>
        )}
      </div>

      {/* Anonymous reporting */}
      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            {...register('is_anonymous')}
            className="w-4 h-4 text-nigeria-green border-gray-300 rounded focus:ring-nigeria-green"
          />
          <span className="text-sm text-gray-700">
            Report anonymously (your contact info will not be stored)
          </span>
        </label>
      </div>

      {/* Submit Button */}
      <div className="flex gap-4 pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={isSubmitting || createMutation.isPending}
          className="flex-1 px-6 py-3 bg-nigeria-green hover:bg-green-700 text-white font-medium rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isSubmitting || createMutation.isPending ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Submitting...
            </span>
          ) : (
            'Submit Report'
          )}
        </button>
      </div>

      {/* Info notice */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> All reports will be reviewed and verified by our team. False
          reports may be flagged or removed.
        </p>
      </div>
    </form>
  );
}
