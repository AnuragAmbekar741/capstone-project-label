import apiClient from "./global.client";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

interface RequestOptions {
  signal?: AbortSignal;
  sendToken?: boolean;
}

const buildConfig = (options?: RequestOptions): AxiosRequestConfig => {
  const config: AxiosRequestConfig = {
    signal: options?.signal,
  };

  // Remove Authorization header if sendToken is false
  if (options?.sendToken === false) {
    config.headers = {
      Authorization: undefined,
    };
  }

  return config;
};

export const get = async <T>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await apiClient.get(endpoint, {
      signal: options?.signal,
    });
    return response.data;
  } catch (error) {
    console.error("GET request error:", error);
    throw error;
  }
};

export const post = async <T, D = unknown>(
  endpoint: string,
  data: D,
  options?: RequestOptions
): Promise<T> => {
  try {
    const config = buildConfig(options);
    const response: AxiosResponse<T> = await apiClient.post(
      endpoint,
      data,
      config
    );
    return response.data;
  } catch (error) {
    console.error("POST request error:", error);
    throw error;
  }
};

export const put = async <T, D = unknown>(
  endpoint: string,
  data: D,
  options?: RequestOptions
): Promise<T> => {
  try {
    const config = buildConfig(options);
    const response: AxiosResponse<T> = await apiClient.put(
      endpoint,
      data,
      config
    );
    return response.data;
  } catch (error) {
    console.error("PUT request error:", error);
    throw error;
  }
};

export const patch = async <T, D = Partial<T>>(
  endpoint: string,
  data: D,
  options?: RequestOptions
): Promise<T> => {
  try {
    const config = buildConfig(options);
    const response: AxiosResponse<T> = await apiClient.patch(
      endpoint,
      data,
      config
    );
    return response.data;
  } catch (error) {
    console.error("PATCH request error:", error);
    throw error;
  }
};

export const del = async <T = void, D = unknown>(
  endpoint: string,
  data?: D,
  options?: RequestOptions
): Promise<T> => {
  try {
    const response: AxiosResponse<T> = await apiClient.delete(endpoint, {
      data,
      signal: options?.signal,
    });
    return response.data;
  } catch (error) {
    console.error("DELETE request error:", error);
    throw error;
  }
};

export const api = {
  get,
  post,
  put,
  patch,
  delete: del,
};
