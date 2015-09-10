var app = angular.module('courseSelectionApp', []);

app.controller('CourseController', ['$scope', '$http', function($scope, $http) {
    $scope.courseList = [];
    $scope.selected = {};

    this.add = function() {
        if($scope.course && $scope.courseList.indexOf($scope.course) === -1) {
            $scope.courseList.push($scope.course);
            console.log($scope.courseList);
        }
    };

    this.go = function() {
        var cc = []
        for(var c in $scope.selected) {
            if ($scope.selected[c]) cc.push(c)
        }
        window.location.href = '/auto/' + $scope.courseList.join() + '/' + cc;
    };

    $scope.updateCourseList = function() {
        $http.get('/dept_info/'+$scope.dept).then(function(res) {
            $scope.courses = res.data.response;
            $scope.course = $scope.courses[0];
        });
    };

    $scope.courses = []
    $http.get('/dept_info').then(function(res) {
        $scope.depts = res.data.response;
        $scope.dept = $scope.depts[0];
        $scope.updateCourseList();
    });
}]);

var sortOrder = ['code', 'c_type', 'section', 'instructor', 'time', 'room', 'max_slots', 'enrolled', 'waitlisted', 'status'];

app.directive('asCourseinfo', function($http, $compile) {
    return {
        scope: false,
        link: function(scope, element, attr) {
            scope.sortOrder = sortOrder;
            $http.get('/course_info/'+scope.course).then(function(res) {
                scope.data = res.data.response;
                console.log(res.data);
                var el = angular.element('<table><tr><th></th><th ng-repeat="field in sortOrder">{{ field }}</tr></table>')
                el.append('<tr ng-repeat="row in data" data-code=\'{{ row["code"] }}\' data-val=\'{{ row["status"] }}\'><td><input type="checkbox" ng-model=\'selected[row["code"]]\' ng-init=\'selected[row["code"]] = row["status"] === "OPEN"\'></td><td ng-repeat="field in sortOrder">{{ row[field] }}</td></tr>');
                $compile(el)(scope);
                element.append(el);
            });
        }
    }
});
