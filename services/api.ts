export const API_CONFIG = {
    BASE_URL:'',
    APY_KEY: process.env.NEXT_PUBLIC_API_KEY,
    headers:{
        accept:'application/json',
        Authorization: `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`
    }
}

export const fetchMovies = ({query}:{query:string}) => {
    const endpoint = ''
}