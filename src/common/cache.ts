import { GetObjectCommand, PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { Config } from './config';

const s3 = new S3Client({ region: Config.region });

interface CacheEntry<T> {
  data: T;
  cachedAt: number;
}

export async function getFromCache<T>(key: string, ttlSeconds: number): Promise<T | null> {
  try {
    const response = await s3.send(
      new GetObjectCommand({
        Bucket: Config.s3Bucket,
        Key: `${key}.json`,
      })
    );

    const body = await response.Body?.transformToString();
    if (!body) return null;

    const entry: CacheEntry<T> = JSON.parse(body);
    const age = (Date.now() - entry.cachedAt) / 1000;

    if (age > ttlSeconds) {
      return null; // Cache expired
    }

    return entry.data;
  } catch {
    return null; // Cache miss or error
  }
}

export async function saveToCache<T>(key: string, data: T): Promise<void> {
  const entry: CacheEntry<T> = {
    data,
    cachedAt: Date.now(),
  };

  await s3.send(
    new PutObjectCommand({
      Bucket: Config.s3Bucket,
      Key: `${key}.json`,
      Body: JSON.stringify(entry),
      ContentType: 'application/json',
    })
  );
}
