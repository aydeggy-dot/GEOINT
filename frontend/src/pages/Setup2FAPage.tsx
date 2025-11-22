/**
 * 2FA Setup Page
 * Enable two-factor authentication with TOTP
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import type { TwoFactorSetupResponse, TwoFactorStatus } from '../types/auth';

export default function Setup2FAPage() {
  const navigate = useNavigate();

  const [status, setStatus] = useState<TwoFactorStatus | null>(null);
  const [setupData, setSetupData] = useState<TwoFactorSetupResponse | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'check' | 'setup' | 'verify' | 'success'>('check');

  useEffect(() => {
    check2FAStatus();
  }, []);

  const check2FAStatus = async () => {
    try {
      const currentStatus = await authService.get2FAStatus();
      setStatus(currentStatus);

      if (currentStatus.enabled) {
        setStep('success');
      } else {
        setStep('setup');
      }
    } catch (err) {
      setError('Failed to check 2FA status');
    }
  };

  const handleSetup2FA = async () => {
    setLoading(true);
    setError('');

    try {
      const data = await authService.setup2FA();
      setSetupData(data);
      setStep('verify');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('2FA setup failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEnable2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.enable2FA(verificationCode);
      setStep('success');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to enable 2FA. Please check your code.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    const password = prompt('Enter your password to disable 2FA:');
    if (!password) return;

    setLoading(true);
    setError('');

    try {
      await authService.disable2FA(password);
      await check2FAStatus();
      setStep('setup');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to disable 2FA');
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadBackupCodes = () => {
    if (!setupData) return;

    const content = `Nigeria Security System - Backup Codes\n\nGenerated: ${new Date().toLocaleString()}\n\n${setupData.backup_codes.join('\n')}\n\n⚠️ Keep these codes safe! Each can only be used once.`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(-1)}
            className="text-blue-600 hover:text-blue-700 mb-4"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            Two-Factor Authentication
          </h1>
          <p className="text-gray-600 mt-2">
            Add an extra layer of security to your account
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Already Enabled */}
        {step === 'success' && status?.enabled && (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                2FA is Enabled
              </h2>
              <p className="text-gray-600">
                Your account is protected with two-factor authentication
              </p>
            </div>

            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-md">
                <p className="text-sm font-medium text-gray-700">Status</p>
                <p className="text-lg text-gray-900">Active</p>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <p className="text-sm font-medium text-gray-700">Method</p>
                <p className="text-lg text-gray-900">TOTP (Authenticator App)</p>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <p className="text-sm font-medium text-gray-700">Backup Codes Remaining</p>
                <p className="text-lg text-gray-900">{status.backup_codes_remaining} codes</p>
              </div>

              <button
                onClick={handleDisable2FA}
                disabled={loading}
                className="w-full bg-red-600 text-white py-3 rounded-md font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors disabled:bg-red-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Disabling...' : 'Disable 2FA'}
              </button>
            </div>
          </div>
        )}

        {/* Setup Step */}
        {step === 'setup' && (
          <div className="bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Enable Two-Factor Authentication
            </h2>

            <div className="space-y-6">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-600 font-bold">
                    1
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Download an authenticator app</h3>
                  <p className="text-gray-600 mt-1">
                    Install Google Authenticator, Authy, or any TOTP-compatible app on your phone
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-600 font-bold">
                    2
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Scan QR code</h3>
                  <p className="text-gray-600 mt-1">
                    Use your authenticator app to scan the QR code we'll provide
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-600 font-bold">
                    3
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">Enter verification code</h3>
                  <p className="text-gray-600 mt-1">
                    Enter the 6-digit code from your app to verify setup
                  </p>
                </div>
              </div>

              <button
                onClick={handleSetup2FA}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-3 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Setting up...' : 'Begin Setup'}
              </button>
            </div>
          </div>
        )}

        {/* Verify Step */}
        {step === 'verify' && setupData && (
          <div className="bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Scan QR Code
            </h2>

            {/* QR Code */}
            <div className="flex justify-center mb-6">
              <img
                src={setupData.qr_code}
                alt="QR Code"
                className="w-64 h-64 border-4 border-gray-200 rounded-lg"
              />
            </div>

            {/* Manual Entry */}
            <div className="bg-gray-50 p-4 rounded-md mb-6">
              <p className="text-sm font-medium text-gray-700 mb-2">Or enter this key manually:</p>
              <code className="block bg-white p-3 rounded border border-gray-300 text-sm font-mono break-all">
                {setupData.secret}
              </code>
            </div>

            {/* Backup Codes */}
            <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-md mb-6">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-yellow-600 mt-0.5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-yellow-800 mb-2">Save Your Backup Codes</h3>
                  <p className="text-sm text-yellow-700 mb-3">
                    Store these codes in a safe place. You can use them to access your account if you lose your device.
                  </p>
                  <div className="bg-white p-3 rounded border border-yellow-300 mb-3">
                    <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                      {setupData.backup_codes.map((code, idx) => (
                        <div key={idx} className="text-gray-700">{code}</div>
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={downloadBackupCodes}
                    className="text-sm text-yellow-700 hover:text-yellow-800 font-medium"
                  >
                    Download codes as text file
                  </button>
                </div>
              </div>
            </div>

            {/* Verification Form */}
            <form onSubmit={handleEnable2FA}>
              <label htmlFor="verificationCode" className="block text-sm font-medium text-gray-700 mb-2">
                Enter 6-digit code from your app
              </label>
              <input
                type="text"
                id="verificationCode"
                value={verificationCode}
                onChange={(e) => {
                  setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                  setError('');
                }}
                required
                maxLength={6}
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest font-mono mb-4"
                placeholder="000000"
                autoFocus
              />

              <button
                type="submit"
                disabled={loading || verificationCode.length !== 6}
                className="w-full bg-blue-600 text-white py-3 rounded-md font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:bg-blue-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Enable 2FA'}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
