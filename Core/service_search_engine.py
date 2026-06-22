class ServiceSearchEngine:
    @staticmethod
    def filter_services(query, services):
        query = query.lower().strip()

        if not query:
            return services

        return [
            s for s in services
            if query in s.lower()
        ]