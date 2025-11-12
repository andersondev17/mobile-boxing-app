export interface Exercise {
  _id: string,
  title: string,
  category: string,
  posterpath: string,
  difficulty: string,
  duration: string,
  description: string,
  technique: string,
  muscles: string[],
  equipment: string;
}

interface TrendingExercise {
  searchTerm: string;
  exercise_id: number;
  title: string;
  count: number;
  poster_url: string;
}

interface ExerciseDetails {
  adult: boolean;
  backdrop_path: string | null;
  belongs_to_collection: {
    id: number;
    name: string;
    poster_path: string;
    backdrop_path: string;
  } | null;
  budget: number;
  genres: {
    id: number;
    name: string;
  }[];
  homepage: string | null;
  id: number;
  imdb_id: string | null;
  original_language: string;
  original_title: string;
  overview: string | null;
  popularity: number;
  poster_path: string | null;
  production_companies: {
    id: number;
    logo_path: string | null;
    name: string;
    origin_country: string;
  }[];
  production_countries: {
    iso_3166_1: string;
    name: string;
  }[];
  release_date: string;
  revenue: number;
  runtime: number | null;
  spoken_languages: {
    english_name: string;
    iso_639_1: string;
    name: string;
  }[];
  status: string;
  tagline: string | null;
  title: string;
  video: boolean;
  vote_average: number;
  vote_count: number;
}

interface TrendingCardProps {
  exercise: TrendingMovie;
  index: number;
}

export interface CVPipelineLandmarks {
  right_shoulder: [number, number];
  right_elbow: [number, number];
  right_wrist: [number, number];
  left_shoulder: [number, number];
  left_elbow: [number, number];
  left_wrist: [number, number];
  angle_r: number;
  angle_l: number;
}

export interface CVPipelineResponse {
  count: number;
  state: 'Esperando' | 'Sube' | 'Bien hecho' | 'Reinicio';
  landmarks?: CVPipelineLandmarks;
}

export interface ProcessVideoResult {
  videoUri: string;
  totalPullups: number;
}
